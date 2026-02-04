import os
import discord
import asyncpg
import datetime
from discord.ext import commands,tasks


# DEFINE INDIAN TIMEZONE (IST) - Exactly like your other file
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# SET LEADERBOARD TIME (e.g., 9:00 PM)
LEADERBOARD_TIME = datetime.time(hour=21, minute=0, tzinfo=IST)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_leaderboard_task.start()
    
    def cog_unload(self):
        # Stop timer if bot shuts down
        self.daily_leaderboard_task.cancel()

    @tasks.loop(time=LEADERBOARD_TIME)
    async def daily_leaderboard_task(self):
        print("IT IS 9:00 PM! Posting Daily Leaderboard...")
        CHANNEL_ID = os.getenv("LEADERBOARD_CHANNEL_ID")
        
        if not CHANNEL_ID:
            print("Error: LEADERBOARD_CHANNEL_ID not found in .env")
            return

        channel = self.bot.get_channel(int(CHANNEL_ID))
        if not channel:
            return

        # Fetch Top 10
        users = await self.bot.db.fetch('''
            SELECT username, score FROM users 
            ORDER BY score DESC LIMIT 10
        ''')

        if not users:
            return # No users registered yet

        # Build the Display
        board_text = "RANK  USER             SCORE\n"
        board_text += "----------------------------\n"

        for rank, user in enumerate(users, 1):
            # Clean the name (cut it if too long)
            name = user['username'][:15]
            score = user['score']
            # Format: Rank (2 digits), Name (15 chars), Score (5 chars)
            board_text += f"#{rank:02d}   {name:<15}  {score:>4}\n"

        # Send as an Embed with a Code Block
        embed = discord.Embed(title="🏆 Daily Standings", color=0x2ECC71) # Green color 
        embed.description = f"```\n{board_text}\n```" # ``` makes it monospaced
        embed.set_footer(text="Updates daily at 9:00 PM IST")
        
        await channel.send(embed=embed)

    

    @commands.command()
    async def post(self, ctx, track: str, difficulty: str, link: str, *, title: str):
        await ctx.message.delete()
        ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
        CHANNEL_ID = int(os.getenv("DAILY_CHALLENGE_CHANNEL_ID"))
        
        if ctx.channel.id != CHANNEL_ID:
            await ctx.send(f"Wrong channel, please go to <#{CHANNEL_ID}>",delete_after=20)
            return 
        
        if ctx.author.id != ADMIN_USER_ID:
            await ctx.send("You are not authorised to use this command",delete_after=20)
            return

        track = track.capitalize()
        difficulty = difficulty.capitalize()

        if track not in ["Beginner", "Advanced"]:
            await ctx.send("Track must be either Beginner or Advanced",delete_after=20)
            return
        if difficulty not in ["Easy", "Medium", "Hard"]:
            await ctx.send("Difficulty must be either Easy, Medium or Hard",delete_after=20)
            return
            
        try:
            await self.bot.db.execute(''' 
                INSERT INTO questions(track, difficulty, link, title, is_posted) 
                VALUES ($1, $2, $3, $4, FALSE)''',
                track, difficulty, link, title
            )
            await ctx.send(f"Queued **{track}** Question: **{title}** ({difficulty})")
        except asyncpg.UniqueViolationError:
            await ctx.send("This question link is already in the database!",delete_after=20)

    @commands.command()
    async def force_today(self, ctx, *, title):
        try: 
            await ctx.message.delete()
        except: 
            pass
        result = await self.bot.db.execute('''
            UPDATE questions SET posted_date = CURRENT_DATE, is_posted = TRUE WHERE title = $1
        ''', title)
        
        if result == "UPDATE 1":
            await ctx.send(f"FORCE UPDATE: **'{title}'** is now marked as Today's Challenge.")
        else:
            await ctx.send(f"Could not find question: **'{title}'**",delete_after=20)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            await ctx.message.delete()
        except:
            pass
        # 1. Ignore "Command Not Found" (User typos)
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Unknown command.Type !help ", delete_after=10)
            return

        

        # 2. Handle Missing Permissions
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that!",delete_after=20)
            return

        # 3. NEW: Handle Missing Arguments (Like forgetting the link)
        if isinstance(error, commands.MissingRequiredArgument):
            if ctx.command.name == "register":
                await ctx.send("**Missing Link!**\nUsage: `!register <leetcode_profile_link>`",delete_after=20)
            elif ctx.command.name == "post":
                await ctx.send("**Missing Info!**\nUsage: `!post <Track> <Difficulty> <Link> <Title>`",delete_after=20)
            else:
                await ctx.send(f"Missing information for command: `{ctx.command.name}`",delete_after=20)
            return

        # 4. Handle CRITICAL Errors (Code Bugs)
        ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
       
        try:
            me = await self.bot.fetch_user(ADMIN_USER_ID)
            error_msg = f"**CRITICAL BOT ERROR** \nCommand: `{ctx.message.content}`\nUser: {ctx.author}\nError: ```{str(error)}```"
            print(error_msg)
            await me.send(error_msg) # Uncomment this if you want DMs for crashes
        except:
            print(f"Could not DM Admin. Error: {error}")
        
        await ctx.send("An internal error occurred. The Admin has been notified.",delete_after=20)

    @daily_leaderboard_task.before_loop
    async def before_leaderboard(self):
        await self.bot.wait_until_ready()
    

async def setup(bot):
    await bot.add_cog(Admin(bot))