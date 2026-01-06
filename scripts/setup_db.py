import os #os bcoz you have to read .env var from dotenv 
import asyncio #it is for async input output opeartions 
import asyncpg #bcoz we need to connect to postgres db asynchronously
from dotenv import load_dotenv

load_dotenv()
password=os.getenv("DB_PASSWORD")

async def test_conn():
    print("TESTING DB CONNECTION...")
    try:
        connection= await asyncpg.connect(
            user="postgres",
            password=password,
            host="127.0.0.1",
            database="ciphers_dev"
        )
        print("CONNECTED NOW CHECKING NEXT STEP...")
        version= await connection.fetchval("SELECT version();")
        print(f"Connected to: {version}")
        
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS users(
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(50) NOT NULL,
                        leetcode_handle VARCHAR(100)UNIQUE NOT NULL,
                        score integer DEFAULT 0

            );
            CREATE TABLE IF NOT EXISTS questions(
                        que_id SERIAL PRIMARY KEY,
                        title VARCHAR(100) NOT NULL,
                        difficulty VARCHAR(20)NOT NULL,
                        link VARCHAR(200)NOT NULL UNIQUE,
                        track VARCHAR(20)NOT NULL,
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
            '''
        )
        await connection.close()


    except Exception as e:
        print("DATABASE CONNECTION FAILED...")

asyncio.run(test_conn())

