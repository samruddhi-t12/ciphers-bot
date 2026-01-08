import os
import discord
import asyncio
import aiohttp
import datetime
from discord.ext import commands

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # RATE LIMITER: Only allow 1 request every 1.5 seconds
        self.leetcode_lock = asyncio.Lock()

    @commands.command()
    async def solved(self, ctx):
        await ctx.message.delete()
        SUBMISSIONS_CHANNEL_ID = int(os.getenv("SUBMISSIONS_CHANNEL_ID"))
        if ctx.channel.id != SUBMISSIONS_CHANNEL_ID:
            await ctx.send(f"Please use <#{SUBMISSIONS_CHANNEL_ID}> to verify solutions!", delete_after=20)
            return
        # 1. FIND USER
        user_row = await self.bot.db.fetchrow('SELECT leetcode_handle FROM users WHERE user_id = $1', ctx.author.id)
        if not user_row:
            await ctx.send(f"{ctx.author.mention}, you are not registered! Type `!register <link>` first.",delete_after=20)
            return
        leetcode_name = user_row['leetcode_handle']
        
        # 2. GET TODAY'S QUESTIONS
        today_questions = await self.bot.db.fetch('SELECT * FROM questions WHERE posted_date = CURRENT_DATE')
        if not today_questions:
            await ctx.send("No Daily Challenge posted today yet!",delete_after=20)
            return
        
        quest_map = {q['title']: q['que_id'] for q in today_questions}
        target_titles = list(quest_map.keys())   
        
        # 3. ASK LEETCODE (SAFE MODE)
        processing_msg = await ctx.send(f"Checking LeetCode for **{leetcode_name}**... (Please wait)")

        async with self.leetcode_lock:
            await asyncio.sleep(1.5) # The Bouncer
            
            query = """
            query getRecentSubmissionList($username: String!) {
              recentSubmissionList(username: $username, limit: 20) {
                title, status, timestamp
              }
            }
            """
            
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                    payload = {"query": query, "variables": {"username": leetcode_name}}
                    
                    async with session.post("https://leetcode.com/graphql", json=payload, headers=headers) as resp:
                        if resp.status != 200:
                            await processing_msg.edit(content="LeetCode is busy (429). Try again in 5 mins.")
                            await processing_msg.delete(delay=10)
                            return
                        data = await resp.json()
                        if "data" not in data or "recentSubmissionList" not in data["data"]:
                            await processing_msg.edit(content="User not found or hidden history.")
                            await processing_msg.delete(delay=10)
                            return
                        recent_subs = data["data"]["recentSubmissionList"]
            except Exception as e:
                print(f"API ERROR: {e}")
                await processing_msg.edit(content="Network Error. The Bot is tired.")
                await processing_msg.delete(delay=10)
                return

        # 4. MATCHING LOGIC
        new_solves = []
        points_added = 0
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_timestamp = today_start.timestamp()

        for sub in recent_subs:
            s_status = str(sub['status']) 
            s_title = sub['title']
            s_time = int(sub['timestamp'])

            if s_status == '10' and s_title in target_titles and s_time >= today_timestamp:
                qid = quest_map[s_title]
                
                existing = await self.bot.db.fetchrow(
                    'SELECT * FROM submissions WHERE user_id=$1 AND que_id=$2', ctx.author.id, qid
                )
                
                if not existing:
                    await self.bot.db.execute(
                        'INSERT INTO submissions (user_id, que_id, status) VALUES ($1, $2, $3)',
                        ctx.author.id, qid, 'Solved'
                    )
                    new_solves.append(s_title)
                    points_added += 10

        await processing_msg.delete()

        if new_solves:
            await self.bot.db.execute('UPDATE users SET score = score + $1 WHERE user_id = $2', points_added, ctx.author.id)
            await ctx.send(f"**VERIFIED!**\nYou solved: **{', '.join(new_solves)}**\n **+{points_added} Points** added to your score!",delete_after=40)
        elif points_added == 0 and any(sub['title'] in target_titles for sub in recent_subs):
            await ctx.send(f"You already claimed points for today's questions!",delete_after=20)
        else:
            await ctx.send(f"**No fresh solution found.**\nMake sure you clicked 'Submit' **today**.",delete_after=20)

async def setup(bot):
    await bot.add_cog(Verification(bot))