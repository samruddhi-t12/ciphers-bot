import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# PASTE YOUR QUESTION LIST HERE
# Format: ("Track", "Difficulty", "Link", "Title")
QUESTION_BANK = [
    
    # --- DAY 1: The Warmup (Arrays) ---
    ("Beginner", "Easy", "https://leetcode.com/problems/contains-duplicate/", "Contains Duplicate"),
    ("Advanced", "Medium", "https://leetcode.com/problems/group-anagrams/", "Group Anagrams"),

    # --- DAY 2: Hashing Logic (Maps) ---
    ("Beginner", "Easy", "https://leetcode.com/problems/majority-element/", "Majority Element"),
    ("Advanced", "Medium", "https://leetcode.com/problems/top-k-frequent-elements/", "Top K Frequent Elements"),

    # --- DAY 3: String Manipulation ---
    ("Beginner", "Easy", "https://leetcode.com/problems/is-subsequence/", "Is Subsequence"),
    ("Advanced", "Medium", "https://leetcode.com/problems/encode-and-decode-strings/", "Encode and Decode Strings"), # (Premium on LC, use LintCode link if needed, or swap for 'Longest Consecutive Sequence')

    # --- DAY 4: Prefix Sums (Important Pattern) ---
    ("Beginner", "Easy", "https://leetcode.com/problems/find-pivot-index/", "Find Pivot Index"),
    ("Advanced", "Medium", "https://leetcode.com/problems/product-of-array-except-self/", "Product of Array Except Self"),

    # --- DAY 5: Logical Thinking ---
    ("Beginner", "Easy", "https://leetcode.com/problems/pascals-triangle/", "Pascal's Triangle"),
    ("Advanced", "Medium", "https://leetcode.com/problems/sort-colors/", "Sort Colors"),

    # --- DAY 6: Weekend Challenge (Bit Harder) ---
    ("Beginner", "Easy", "https://leetcode.com/problems/next-greater-element-i/", "Next Greater Element I"),
    ("Advanced", "Medium", "https://leetcode.com/problems/longest-consecutive-sequence/", "Longest Consecutive Sequence"),

    # --- DAY 7: Revision / Mixed Bag ---
    ("Beginner", "Easy", "https://leetcode.com/problems/valid-anagram/", "Valid Anagram"),
    ("Advanced", "Medium", "https://leetcode.com/problems/subarray-sum-equals-k/", "Subarray Sum Equals K"),
]

async def seed_db():
    print("Seeding Database...")
    try:
        conn = await asyncpg.connect(
            user="postgres",
            password=os.getenv("DB_PASSWORD"),
            host="127.0.0.1",
            database="ciphers_dev"
        )
        
        count = 0
        for q in QUESTION_BANK:
            track, diff, link, title = q
            try:
                await conn.execute('''
                    INSERT INTO questions (track, difficulty, link, title, is_posted)
                    VALUES ($1, $2, $3, $4, FALSE)
                ''', track, diff, link, title)
                print(f"Added: {title}")
                count += 1
            except asyncpg.UniqueViolationError:
                print(f"⚠️ Skipped (Duplicate): {title}")
        
        print(f"\nProcess Complete! Added {count} new questions.")
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(seed_db())