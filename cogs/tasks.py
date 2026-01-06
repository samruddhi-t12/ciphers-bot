import os
import discord
import datetime
import asyncio
from discord.ext import commands, tasks

# 1. DEFINE INDIAN TIMEZONE (IST)
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
# 2. SET THE EXACT TIME (e.g., 8:00 AM)
POST_TIME = datetime.time(hour=8, minute=0, tzinfo=IST)
class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_load(self):
        # Start the loop when this Cog loads
        self.daily_post_task.start()

    @tasks.loop(time=POST_TIME)
    async def daily_post_task(self):
       
        print("IT IS 8:00 AM! Checking for questions to post...")
        DAILY_CHALLENGE_CHANNEL_ID = int(os.getenv("DAILY_CHALLENGE_CHANNEL_ID"))
        DISCUSSION_CHANNEL_ID = int(os.getenv("DISCUSSION_CHANNEL_ID"))   
        
        chall_channel = self.bot.get_channel(DAILY_CHALLENGE_CHANNEL_ID)
        disc_channel = self.bot.get_channel(DISCUSSION_CHANNEL_ID)
        
        if not chall_channel or not disc_channel:
            print("ONE OF THE CHANNELS was NOT FOUND")
            return
        
        # Fetch Questions
        beg_row = await self.bot.db.fetchrow('''
            SELECT * FROM questions WHERE is_posted = FALSE AND track = 'Beginner' ORDER BY que_id ASC LIMIT 1
        ''')
        adv_row = await self.bot.db.fetchrow('''
            SELECT * FROM questions WHERE is_posted = FALSE AND track = 'Advanced' ORDER BY que_id ASC LIMIT 1
        ''')

        if beg_row and adv_row:
            date_str = datetime.datetime.now(IST).strftime("%d %b %Y")
            message = (
                f"**Daily Challenge - {date_str}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**Beginner:** [{beg_row['title']}]({beg_row['link']})\n"
                f"*Difficulty: {beg_row['difficulty']}*\n\n"
                f"**Advanced:** [{adv_row['title']}]({adv_row['link']})\n"
                f"*Difficulty: {adv_row['difficulty']}*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"*Discussion channel is LOCKED for 20 mins to prevent spoilers!*"
            )

            await chall_channel.send(message)
            
            # Update DB
            await self.bot.db.execute('UPDATE questions SET is_posted=TRUE, posted_date=CURRENT_DATE WHERE que_id=$1', beg_row['que_id'])
            await self.bot.db.execute('UPDATE questions SET is_posted=TRUE, posted_date=CURRENT_DATE WHERE que_id=$1', adv_row['que_id'])
            
            # Locking Logic
            try:
                guild = disc_channel.guild
                default_role = guild.default_role
                await disc_channel.set_permissions(default_role, send_messages=False)
                await disc_channel.send("**Channel Locked for 20 mins! Solve the problem first.**")

            # Wait 20 mins
                await asyncio.sleep(1200)

            # Unlock
                await disc_channel.set_permissions(default_role, send_messages=True)
                await disc_channel.send("**Channel Unlocked! Discuss all your doubts.**")
            
            except Exception as e:
                print(f"Error in locking/unlocking channel: {e}")
        else:
            print("Queue Incomplete: Need 1 beginner and 1 advanced question.")

    @daily_post_task.before_loop
    async def before_daily_post(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Tasks(bot))