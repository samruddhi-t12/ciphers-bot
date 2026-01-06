import os 
import asyncio 
import asyncpg 
from dotenv import load_dotenv

load_dotenv()

# 1. Get the Cloud Link from .env
DB_URL = os.getenv("DATABASE_URL")

async def setup_cloud_db():
    print("CONNECTING TO NEON CLOUD...")
    
    if not DB_URL:
        print("ERROR: DATABASE_URL not found in .env file!")
        return

    try:
        # 2. Connect using the Cloud Link
        # ssl='require' is standard for cloud databases
        connection = await asyncpg.connect(dsn=DB_URL)
        
        print("CONNECTED! Creating Tables now...")
        
        # 3. Create the Tables
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                leetcode_handle VARCHAR(100) UNIQUE NOT NULL,
                score integer DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS questions(
                que_id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                difficulty VARCHAR(20) NOT NULL,
                link VARCHAR(200) NOT NULL UNIQUE,
                track VARCHAR(20) NOT NULL,
                is_posted BOOLEAN DEFAULT FALSE,
                posted_date DATE
            );

            CREATE TABLE IF NOT EXISTS submissions(
                sub_id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                que_id INTEGER REFERENCES questions(que_id) ON DELETE CASCADE,
                submiited_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR DEFAULT 'Pending'
            );
        ''')
        
        print("SUCCESS! All tables created on Neon Cloud.")
        
        # Verify version just to be cool
        version = await connection.fetchval("SELECT version();")
        print(f"Database Version: {version}")
        
        await connection.close()

    except Exception as e:
        print(f"DATABASE ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(setup_cloud_db())