# 🛡️ CIPHERS Bot - Automated DSA Challenge System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Discord](https://img.shields.io/badge/Discord.py-2.0-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon.tech-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Cloud](https://img.shields.io/badge/Deployed_on-Render-black?style=for-the-badge&logo=render&logoColor=white)

> **The Official DSA Training Bot for the CIPHERS Club.**  > *Automating consistency, gamifying progress, and building a coding culture.*

---

## 📖 Overview
CIPHERS Bot is a custom-built discord automation tool designed to help students maintain a daily streak of Data Structures & Algorithms (DSA) practice. 

It solves the problem of "inconsistency" by automating the entire flow: from posting daily curated questions (Beginner & Advanced) to verifying submissions and generating real-time leaderboards.

## ✨ Key Features

### 🤖 Automation & Logic
* **Daily Scheduler:** Automatically posts 2 LeetCode problems (Easy/Medium) every day at **8:00 AM IST**.
* **Spoiler Protection:** Automatically **locks** the discussion channel for 20 minutes after posting to encourage independent solving.
* **Keep-Alive Architecture:** Uses a background Flask microservice to ensure 24/7 uptime on Cloud Free Tiers.

### ⚔️ Gamification
* **Registration System:** Links a user's Discord ID to their LeetCode profile via `!register`.
* **Smart Verification:** Users type `!solved` to verify their submissions. The bot checks their LeetCode history to confirm.
* **Live Leaderboard:** A dynamic `!leaderboard` that ranks students based on consistency and difficulty.

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.10 | Core logic and async handling |
| **Framework** | Discord.py | Interaction with Discord API |
| **Database** | PostgreSQL (Neon) | Persistent storage for users, scores, and question bank |
| **Hosting** | Render Cloud | CI/CD deployment from GitHub |
| **Uptime** | Flask + UptimeRobot | Prevents cloud instance from sleeping |

---

## 🚀 How to Run Locally

If you want to contribute or test this bot, follow these steps:

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/ciphers-bot.git](https://github.com/YOUR_USERNAME/ciphers-bot.git)
cd ciphers-bot
```
### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
### 3. Setup Environment Variables
Create a .env file in the root directory and add your secrets:

```Code snippet

DISCORD_TOKEN=your_bot_token
DATABASE_URL=your_neon_db_url
ADMIN_CHANNEL_ID=123456...
REGISTRATION_CHANNEL_ID=123456...
SUBMISSION_CHANNEL_ID=123456...
STUDENT_CHANNEL_ID=123456....
```
### 4. Run the Bot
```bash
python main.py
```

---
<p align="center">
  Fueled by ☕ and late-night debugging by <b>Samruddhi</b> 💻<br/>
  Connect with me on <a href="https://www.linkedin.com/in/samruddhi-thorat-90b103286/">LinkedIn</a>
</p>

