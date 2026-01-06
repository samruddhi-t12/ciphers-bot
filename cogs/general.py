import os
import discord
from discord.ext import commands
import asyncpg

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def register(self, ctx, link: str):
        await ctx.message.delete()
        REGISTERATION_CHANNEL_ID = int(os.getenv("REGISTERATION_CHANNEL_ID"))
        
        if ctx.channel.id != REGISTERATION_CHANNEL_ID:
            await ctx.send(f"Wrong channel, Please go to <#{REGISTERATION_CHANNEL_ID}> to register",delete_after=20)
            return
        link = link.replace("<", "").replace(">", "")
        if "leetcode.com" not in link:
            await ctx.send("Please provide a valid leetcode link",delete_after=20)
            return

        clean_link = link.rstrip("/")
        leetcode_username = clean_link.split("/")[-1]
        
        msg=await ctx.send(f"checking availability for: **{leetcode_username}**",delete_after=20)
        
        try:
            await self.bot.db.execute('''
                INSERT INTO users(user_id, username, leetcode_handle, score) 
                VALUES ($1, $2, $3, 0)
            ''', ctx.author.id, ctx.author.name, leetcode_username)
            await msg.delete()
            await ctx.send(f"Successfully registered **{leetcode_username}** !")

        except asyncpg.UniqueViolationError:
            await msg.delete()
            await ctx.send("You are already registered!",delete_after=20)
        except Exception as e:
            await msg.delete()
            await ctx.send(f"error occurred: {e}",delete_after=20)

    @commands.command()
    async def profile(self, ctx, member: discord.Member = None):
        await ctx.message.delete()
        target = member or ctx.author
        discussion_channel_id = int(os.getenv("DISCUSSION_CHANNEL_ID"))
        if ctx.channel.id != discussion_channel_id:
            # Delete their wrong message instantly
            await ctx.message.delete()
            # Send a disappearing warning
            await ctx.send(f"Please use <#{discussion_channel_id}> to check profile!", delete_after=10)
            return
        user = await self.bot.db.fetchrow('SELECT * FROM users WHERE user_id = $1', target.id)
        
        if not user:
            msg = "You are" if target == ctx.author else f"{target.display_name} is"
            await ctx.send(f"{msg} not registered!")
            return
            
        embed = discord.Embed(title=f"👤 CIPHERS Profile", color=discord.Color.blue())
        embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
        embed.add_field(name="Name", value=target.display_name, inline=True)
        embed.add_field(name="LeetCode", value=f"[{user['leetcode_handle']}](https://leetcode.com/{user['leetcode_handle']})", inline=True)
        embed.add_field(name="", value="", inline=False) 
        embed.add_field(name="Total Score", value=f"**{user['score']} Points**", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def leaderboard(self, ctx):
        await ctx.message.delete()
        discussion_channel_id = int(os.getenv("DISCUSSION_CHANNEL_ID"))
        if ctx.channel.id != discussion_channel_id:
            # Delete their wrong message instantly
            await ctx.message.delete()
            # Send a disappearing warning
            await ctx.send(f"Please use <#{discussion_channel_id}> to see leaderboard!", delete_after=10)
            return
        top_users = await self.bot.db.fetch('''
            SELECT leetcode_handle, score FROM users ORDER BY score DESC LIMIT 10
        ''')
        
        if not top_users:
            await ctx.send("The Leaderboard is currently empty!",delete_after=20)
            return

        msg = "**🏆 CIPHERS DSA LEADERBOARD 🏆**\n```md\n"
        msg += f"{'Rank':<5} {'Name':<20} {'Score':<5}\n"
        msg += "-" * 35 + "\n"
        
        for i, user in enumerate(top_users, 1):
            name = user['leetcode_handle'][:19]
            score = user['score']
            msg += f"{i:<5} {name:<20} {score:<5}\n"
        
        msg += "```\n"
        await ctx.send(msg)

    


    @commands.command()
    async def help(self, ctx):
        await ctx.message.delete()
        # Get Channel IDs from .env to make clickable links
        reg_channel = os.getenv("REGISTRATION_CHANNEL_ID")
        sub_channel = os.getenv("SUBMISSION_CHANNEL_ID")
        discuss_channel = os.getenv("DISCUSSION_CHANNEL_ID")

        embed = discord.Embed(title="CIPHERS Bot Guide", description="Here is where to use each command:", color=discord.Color.green())
        
        # 1. Registration
        embed.add_field(
            name="Registration", 
            value=f"`!register <leetcode_link>`\n**Where:** <#{reg_channel}>", 
            inline=False
        )
        
        # 2. Submission
        embed.add_field(
            name="Verify Solution", 
            value=f"`!solved` (or `!submit`)\n**Where:** <#{sub_channel}>", 
            inline=False
        )
        
        # 3. Stats & Profile
        embed.add_field(
            name="Stats", 
            value=f"`!leaderboard` & `!profile`\n**Where:** <#{discuss_channel}>", 
            inline=False
        )
        
        embed.set_footer(text="Keep grinding! ")
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(General(bot))