
# Discord Activity Tracker Bot

This bot tracks the number of messages each user sends in a Discord server and stores the data in a Supabase database for persistence.

## Features

- **Track User Messages**: Automatically increments each user’s message count.  
- **Individual Stats**: Use `!activity` to see how many messages you (or another user) have sent.  
- **Leaderboard**: Use `!allactivity` to list message counts for all tracked users.  
- **Persistent Storage**: All data is stored in a Supabase table (instead of an in-memory dictionary).

## Prerequisites

1. **Python 3.8+**  
2. **A Discord Bot**: [Discord Developer Portal](https://discord.com/developers/applications) to create your bot token.  
   - Enable **Message Content Intent** in the bot settings.  
3. **Supabase Account**: Create a `user_activity` table:
   ```sql
   CREATE TABLE IF NOT EXISTS user_activity (
     user_id TEXT PRIMARY KEY,
     count INT
   );
   ```
4. **Dependencies**: `py-cord`, `python-dotenv`, `supabase`.

## Setup

1. **Clone the repository** and create a file named `.env` in the project folder with:
   ```bash
   BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
   SUPABASE_URL=https://YOUR_PROJECT.supabase.co
   SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_OR_SERVICE_KEY
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Or:
   ```bash
   pip install py-cord python-dotenv supabase
   ```
3. **Run the bot**:
   ```bash
   python bot.py
   ```

## Usage

1. **Invite the Bot** to your server using the generated OAuth2 link from the Developer Portal.  
2. In Discord:
   - Type `!activity` to view your personal message count.  
   - Type `!activity @User` to view another user’s count.  
   - Type `!allactivity` to see the leaderboard.

## Contributing

- **Fork** this repository.
- Create a **feature branch**, make your changes.
- Submit a **pull request** describing your updates.

---

