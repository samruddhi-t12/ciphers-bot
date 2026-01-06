import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from database import Database
from keep_alive import keep_alive

load_dotenv()

class CiphersBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        self.db = Database() # Initialize our custom DB class

    async def setup_hook(self):
        # 1. Connect to Database
        await self.db.connect()
        
        # 2. Load Cogs (The Modules)
        # It looks for files in the 'cogs' folder
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and filename != '__init__.py':
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"Loaded Cog: {filename}")

                except Exception as e:
                    print(f"Failed to load cog {filename}: {e}")
                

    async def on_ready(self):
        print(f"SYSTEM READY: Logged in as {self.user}")

    async def close(self):
        await self.db.close()
        await super().close()
        print("SYSTEM SHUTDOWN: Database disconnected.")

# RUNNER
if __name__ == "__main__": 
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("CRITICAL ERROR: DISCORD_TOKEN not found in .env file")
    else:
        keep_alive()
        try:
            bot = CiphersBot()
            bot.run(token)
        except KeyboardInterrupt:
            # This catches Ctrl+C nicely
            pass