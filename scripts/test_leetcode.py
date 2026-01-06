import aiohttp
import asyncio

QUERY = """
query getRecentSubmissionList($username: String!) {
  recentSubmissionList(username: $username, limit: 20) {
    title
    titleSlug
    status
    timestamp
  }
}
"""



async def check_user(username):
    url = "https://leetcode.com/graphql"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # FIX: Remove the trailing slash FIRST, then split
    if "leetcode.com" in username:
        username = username.rstrip("/").split("/")[-1]

    # Print this so we can see EXACTLY what username it is searching for
    print(f" Checking LeetCode for: '{username}'...") 

    payload = {
        "query": QUERY,
        "variables": {"username": username}
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                print(f"Error: Status Code {response.status}")
                return
            
            data = await response.json()
            
            if "data" not in data or "recentSubmissionList" not in data["data"]:
                print("Data Structure Mismatch.")
                return

            submissions = data["data"]["recentSubmissionList"]
            
            print(f"Found {len(submissions)} recent submissions!")
            print("-" * 30)
            
            for sub in submissions:
                # PRINT THE RAW STATUS so we can see what it really is
                raw_status = sub['status']
                print(f"Status: [{raw_status}] | Title: {sub['title']}")
# --- TEST ---
# Make sure this is JUST the username (e.g., "rohit_123")
asyncio.run(check_user("https://leetcode.com/u/BeyondTheLoop/"))