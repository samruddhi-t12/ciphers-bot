import asyncpg
import os

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        print("Connecting to Database...")
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            #CLOUD MODE (This runs when use Neon)
            # ssl='require' is usually needed for cloud databases
            self.pool = await asyncpg.create_pool(dsn=db_url)
            print("Connected to NEON Cloud Database")
        else:
            # LOCAL MODE (This runs on laptop if no link is found)
            self.pool = await asyncpg.create_pool(
                user="postgres",
                password=os.getenv("DB_PASSWORD"),
                host="127.0.0.1",
                database="ciphers_dev"
            )
            print("Connected to Local Database")
        
    # Helper methods to make queries cleaner in other files
    async def fetch(self, query, *args):
        return await self.pool.fetch(query, *args)

    async def fetchrow(self, query, *args):
        return await self.pool.fetchrow(query, *args)

    async def execute(self, query, *args):
        return await self.pool.execute(query, *args)
    

    async def close(self):
        await self.pool.close()