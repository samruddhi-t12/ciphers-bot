import asyncio
import os
import discord
import asyncpg
import datetime
import aiohttp
from discord.ext import commands
from discord.ext import tasks
from dotenv import load_dotenv


IST=datetime.timezone(datetime.timedelta(hours=5,minutes=30))
POST_TIME=datetime.time(hour=8,minute=0,tzinfo=IST)

# RATE LIMITER: Only allow 1 request every 2 seconds
leetcode_lock = asyncio.Lock()

load_dotenv()
class CiphersBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content=True
        super().__init__(command_prefix='!', intents=intents,help_command=None)
        self.db=None
    async def setup_hook(self):
        print("CONNECTING TO DB")
        self.db= await asyncpg.create_pool(
            user="postgres",
            password=os.getenv("DB_PASSWORD"),
            host="127.0.0.1",
            database="ciphers_dev"
        )
        print("DB CONNECTED")
        self.daily_post_task.start()


    async def on_ready(self):
        print(f"SYSTEM READY logged in as {self.user}")

    @tasks.loop(seconds=300)
    async def daily_post_task(self):
        print ("ROUTINE CHECK :ATTEMPTING TO POST DAILY QUESTIONS")
        #we are taking channel ids to do lock n post intto that specific channel itself
        DAILY_CHALLENGE_CHANNEL_ID = int(os.getenv("DAILY_CHALLENGE_CHANNEL_ID"))
        DISCUSSION_CHANNEL_ID = int(os.getenv("DISCUSSION_CHANNEL_ID"))   
        
        
        #now we are taking new var bcoz we wanna use in python code? or do we have any other use of this that idk???
        chall_channel=self.get_channel(DAILY_CHALLENGE_CHANNEL_ID)
        disc_channel = self.get_channel(DISCUSSION_CHANNEL_ID)
        #now we are gonna check if we can fetch those channels first?
        if not chall_channel or not disc_channel:
            print("ONE OF THE CHANNELs was NOT FOUND")
            return
        
        # 2. Fetch Questions (One for each track)
        beg_row = await self.db.fetchrow('''
            SELECT * FROM questions WHERE is_posted = FALSE AND track = 'Beginner' 
            ORDER BY que_id ASC LIMIT 1
        ''')
        
        adv_row = await self.db.fetchrow('''
            SELECT * FROM questions WHERE is_posted = FALSE AND track = 'Advanced' 
            ORDER BY que_id ASC LIMIT 1
        ''')

        #here we are checking if questions present n if yes or notwhat to do?
        if beg_row and adv_row:
            # Prepare Data
            #datetime_now fetching current date n time of server 
            #strftime is formating date here d is day b is month in short form n Y is year in 4 digit 
            date_str = datetime.datetime.now().strftime("%d %b %Y")
            message = (
                f"**Daily Challenge - {date_str}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**Beginner:** [{beg_row['title']}]({beg_row['link']})\n"#this formatting beg_row n all those brackets are for markdown formatting in discord
                f"*Difficulty: {beg_row['difficulty']}*\n\n"
                f"**Advanced:** [{adv_row['title']}]({adv_row['link']})\n"
                f"*Difficulty: {adv_row['difficulty']}*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"*Discussion channel is LOCKED for 20 mins to prevent spoilers!*"
            )


            await chall_channel.send(message)#this is sending message but what does await do here ? why we use await ?->await is waiting for discord server to respond back after sending message before going to next line of code
            # ADD "posted_date = CURRENT_DATE"
            await self.db.execute('UPDATE questions SET is_posted=TRUE, posted_date=CURRENT_DATE WHERE que_id=$1', beg_row['que_id'])
            await self.db.execute('UPDATE questions SET is_posted=TRUE, posted_date=CURRENT_DATE WHERE que_id=$1', adv_row['que_id'])
            print(f"Posted: {beg_row['title']} & {adv_row['title']}")

            print("Locking Discussion Channel for 20 minutes to prevent spoilers...")

            # Get the '@everyone' role (it's always the default role of the guild)
            guild=disc_channel.guild # what is this guild ?-> fancy name for discord server 
            default_role=guild.default_role #it's for role in discord? -> default role is @everyone role

            # Lock it (Send Messages = False)
            await disc_channel.set_permissions(default_role, send_messages=False)
            await disc_channel.send("**Channel Locked for 20 mins! Solve the problem first.**")

            # WAIT (For testing: 60 seconds. For Real: 1200 seconds)
            await asyncio.sleep(180)#asyncio used for?->it is for parallel execution it is not blocking other operations while waiting one task to complete

            # Unlock it
            await disc_channel.set_permissions(default_role, send_messages=True)
            await disc_channel.send("**Channel Unlocked! Discuss all your doubts and solutions with your DSA Buddies**")
            print("Discussion Unlocked.")


        else:
            print("Queue Incomplete:Need 1 beginner and 1 advanced question to post daily challenges.")


    @daily_post_task.before_loop
    async def before_daily_post(self):
        await self.wait_until_ready()#here idk what it is doing ?is it waiting for bot to be ready or what? -> yeah it is waiting to load discord server n bot completely before starting the task loop

bot=CiphersBot()
token=os.getenv("DISCORD_TOKEN")


@bot.command()
async def register(ctx,link:str):
    REGISTERATION_CHANNEL_ID=int(os.getenv("REGISTERATION_CHANNEL_ID"))
    if ctx.channel.id!=REGISTERATION_CHANNEL_ID:
        await ctx.send(f"Wrong channel,Please go to <#{REGISTERATION_CHANNEL_ID}> to register")
        return
    if "leetcode.com" not in link:
        await ctx.send("Please provide a valid leetcode link")
        return
    clean_link=link.rstrip("/")
    leetcode_username=clean_link.split("/")[-1]
    await ctx.send(f"checking avaialability for: **{leetcode_username}**")
    try:
        await bot.db.execute('''
                             INSERT INTO users(user_id,username,leetcode_handle,score) values ($1,$2,$3,0)''',
                             ctx.author.id,
                             ctx.author.name,
                             leetcode_username
        )
        await ctx.send(f"Successfully registered **{leetcode_username}** !")

    except asyncpg.UniqueViolationError:
        await ctx.send("You are already registered!")
    except Exception as e:
        await ctx.send(f"error occured: {e}")

@bot.command()
async def post(ctx,track:str,difficulty:str,link:str,*,title:str):
    await ctx.message.delete()
    ADMIN_USER_ID=int(os.getenv("ADMIN_USER_ID"))
    CHANNEL_ID=int(os.getenv("DAILY_CHALLENGE_CHANNEL_ID"))
    if ctx.channel.id!=CHANNEL_ID:
        await ctx.send(f"Wrong channel,Please go to <#{CHANNEL_ID}> to post questions")
        return 
    
    if ctx.author.id!=ADMIN_USER_ID:
        await ctx.send("You are not authorised to use this command")
        return
    track=track.capitalize()
    difficulty=difficulty.capitalize()

    if track not in ["Beginner","Advanced"]:
        await ctx.send("Track must be either Beginner or Advanced")
        return
    if difficulty not in ["Easy","Medium","Hard"]:
        await ctx.send("Difficulty must be either Easy,Medium or Hard")
        return
    try:
        await bot.db.execute(''' 
                             INSERT INTO questions(track,difficulty,link,title,is_posted) values ($1,$2,$3,$4,FALSE)''',
                             track,
                             difficulty,
                             link,
                             title
        )
        await ctx.send(f"Queued **{track}** Question: **{title}** ({difficulty})")
    except asyncpg.UniqueViolationError:
        await ctx.send("This question link is already in the database!")

@post.error
async def post_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "**Missing Information!**\n"
            "Correct Usage:\n"
            "`!post <Track> <Difficulty> <Link> <Title>`\n"
            "Example: `!post Beginner Easy https://leetcode.com/... Two Sum`",
            delete_after=10
        )
    else:
        # If it's some other weird error, print it so we know
        await ctx.send(f"Something went wrong: {error}")

@bot.command()
async def solved(ctx):
    # 1. FIND USER
    user_row = await bot.db.fetchrow('SELECT leetcode_handle FROM users WHERE user_id = $1', ctx.author.id)
    if not user_row:
        await ctx.send(f"{ctx.author.mention}, you are not registered! Type `!register <link>` first.")
        return
    leetcode_name = user_row['leetcode_handle']
    
    # 2. GET TODAY'S QUESTIONS
    today_questions = await bot.db.fetch('SELECT * FROM questions WHERE posted_date = CURRENT_DATE')
    if not today_questions:
        await ctx.send("No Daily Challenge posted today yet!")
        return
    
    quest_map = {q['title']: q['que_id'] for q in today_questions}
    target_titles = list(quest_map.keys())   
    
    # 3. ASK LEETCODE (SAFE MODE )
    processing_msg = await ctx.send(f"Checking LeetCode for **{leetcode_name}**... (Please wait)")

    # THE BOUNCER IS HERE 
    async with leetcode_lock:
        # We wait our turn here. If 50 people command, they queue up here.
        await asyncio.sleep(1.5) # Force a 1.5 second pause between EACH request.
        
        query = """
        query getRecentSubmissionList($username: String!) {
          recentSubmissionList(username: $username, limit: 20) {
            title
            status
            timestamp
          }
        }
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                payload = {"query": query, "variables": {"username": leetcode_name}}
                
                async with session.post("https://leetcode.com/graphql", json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        await processing_msg.edit(content="LeetCode is busy (429). Try again in 5 mins.")
                        return
                    
                    data = await resp.json()
                    if "data" not in data or "recentSubmissionList" not in data["data"]:
                        await processing_msg.edit(content="User not found or hidden history.")
                        return
                    recent_subs = data["data"]["recentSubmissionList"]
        except Exception as e:
            print(f"API ERROR: {e}")
            await processing_msg.edit(content="Network Error. The Bot is tired.")
            return

    # 4. MATCHING LOGIC (Rest is the same...)
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
            
            existing = await bot.db.fetchrow(
                'SELECT * FROM submissions WHERE user_id=$1 AND que_id=$2', 
                ctx.author.id, qid
            )
            
            if not existing:
                await bot.db.execute(
                    'INSERT INTO submissions (user_id, que_id, status) VALUES ($1, $2, $3)',
                    ctx.author.id, qid, 'Solved'
                )
                new_solves.append(s_title)
                points_added += 10

    await processing_msg.delete()

    if new_solves:
        await bot.db.execute('UPDATE users SET score = score + $1 WHERE user_id = $2', points_added, ctx.author.id)
        await ctx.send(f"**VERIFIED!**\nYou solved: **{', '.join(new_solves)}**\n **+{points_added} Points** added to your score!")
    elif points_added == 0 and any(sub['title'] in target_titles for sub in recent_subs):
        await ctx.send(f"You already claimed points for today's questions!")
    else:
        await ctx.send(f"**No fresh solution found.**\nMake sure you clicked 'Submit' **today**.")

@bot.command()
async def force_today(ctx, *, title):
    # This command forces a specific question to be "Today's Challenge"
    # Usage: !force_today Word Search
    
    result = await bot.db.execute('''
        UPDATE questions 
        SET posted_date = CURRENT_DATE, is_posted = TRUE 
        WHERE title = $1
    ''', title)
    
    if result == "UPDATE 1":
        await ctx.send(f"FORCE UPDATE: **'{title}'** is now marked as Today's Challenge.")
    else:
        await ctx.send(f"Could not find question: **'{title}'** (Check spelling exactly!)")


@bot.command()
async def leaderboard(ctx):
    # 1. Fetch Top 10 Users
    top_users = await bot.db.fetch('''
        SELECT leetcode_handle, score 
        FROM users 
        ORDER BY score DESC 
        LIMIT 10
    ''')
    
    if not top_users:
        await ctx.send("The Leaderboard is currently empty!")
        return

    # 2. Build the Message Table
    # We use a Code Block (```) to make it look aligned like a table
    msg = "**🏆 CIPHERS DSA LEADERBOARD 🏆**\n```md\n"
    msg += f"{'Rank':<5} {'Name':<20} {'Score':<5}\n"
    msg += "-" * 35 + "\n"
    
    for i, user in enumerate(top_users, 1):
        # Format: "1.    rohit_king           150  "
        name = user['leetcode_handle'][:19] # Cut name if too long
        score = user['score']
        msg += f"{i:<5} {name:<20} {score:<5}\n"
    
    msg += "```\n"
    msg += f"*Check the full list on our website: https://YOUR_NETLIFY_LINK.app*"
    
    await ctx.send(msg)  

# Remove default help command first
bot.remove_command('help')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="CIPHERS Bot Command List", description="Here is how to use the Daily DSA Bot:", color=discord.Color.green())
    
    embed.add_field(name="Registration", value="`!register <leetcode_link>`\nLink your LeetCode profile to start.", inline=False)
    embed.add_field(name="Verify Solution", value="`!solved`\nType this AFTER you submit your code on LeetCode.", inline=False)
    embed.add_field(name="Leaderboard", value="`!leaderboard`\nSee the Top 10 players.", inline=False)
    embed.add_field(name="Profile", value="`!profile`\nCheck your own stats.", inline=False)
    
    embed.set_footer(text="Happy Coding! ")
    await ctx.send(embed=embed)

@bot.command()
async def profile(ctx, member: discord.Member = None):
    # If no user is mentioned, default to the person who typed the command
    target = member or ctx.author
    
    # Fetch user data from DB
    user = await bot.db.fetchrow('SELECT * FROM users WHERE user_id = $1', target.id)
    
    if not user:
        if target == ctx.author:
            await ctx.send(f"You are not registered! Use `!register <link>` first.")
        else:
            await ctx.send(f"{target.display_name} is not registered yet!")
        return
        
    # Create a nice looking card (Embed)
    embed = discord.Embed(
        title=f"👤 CIPHERS Profile", 
        color=discord.Color.blue()
    )
    
    # Add their Discord Profile Pic as the thumbnail
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    
    embed.add_field(name="Name", value=target.display_name, inline=True)
    embed.add_field(name="LeetCode", value=f"[{user['leetcode_handle']}](https://leetcode.com/{user['leetcode_handle']})", inline=True)
    
    # Empty field to force a line break (makes it look cleaner)
    embed.add_field(name="", value="", inline=False) 
    
    embed.add_field(name="Total Score", value=f"**{user['score']} Points**", inline=True)
    # You can add Rank here later if you want (requires a complex query)
    
    embed.set_footer(text="Keep solving to increase your score!")
    
    await ctx.send(embed=embed)
    
@bot.event
async def on_command_error(ctx, error):
    # 1. Ignore "Command Not Found" (User typos)
    if isinstance(error, commands.CommandNotFound):
        return

    # 2. Handle "Missing Permissions" (User tries Admin command)
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to do that!")
        return

    # 3. Handle CRITICAL Errors (Code Bugs)
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))
    MY_ID = ADMIN_USER_ID
    try:
        me = await bot.fetch_user(MY_ID)
        error_msg = f"**CRITICAL BOT ERROR** \nCommand: `{ctx.message.content}`\nUser: {ctx.author}\nError: ```{str(error)}```"
        print(error_msg)
        await me.send(error_msg)
    except:
        print(f"Could not DM Admin. Error: {error}")
    
    await ctx.send("An internal error occurred. The Admin has been notified.")


# 2. RUN THE BOT LAST
if token:
    bot.run(token)
else:
    print("DISCORD TOKEN NOT FOUND")