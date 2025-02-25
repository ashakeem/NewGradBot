import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from supabase import create_client, Client

# 1. Load environment variables from .env
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")              # Discord bot token
SUPABASE_URL = os.getenv("SUPABASE_URL")    # e.g. "https://abccompany.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # or use SERVICE_ROLE_KEY if needed

# 2. Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Set up Discord Intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Needed to read message content

# 4. Create the Bot
bot = commands.Bot(command_prefix="!", intents=intents)

###################################################################
#                   EVENTS & COMMANDS BELOW
###################################################################

@bot.event
async def on_ready():
    """Called when the bot has successfully connected to Discord."""
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message):
    """
    Tracks user messages in Supabase.
    Whenever a user sends a message, we increment their count in the DB.
    """
    # Avoid counting the bot's own messages
    if message.author == bot.user:
        return

    user_id = str(message.author.id)  # store as text for the DB

    # 1. Fetch existing record for this user
    data = supabase.table("user_activity").select("*").eq("user_id", user_id).execute()

    if data.data:
        # If found, increment the count
        current_count = data.data[0]["count"]
        new_count = current_count + 1

        # Update the existing row
        supabase.table("user_activity").update({"count": new_count}).eq("user_id", user_id).execute()
    else:
        # If not found, create a new row with count = 1
        supabase.table("user_activity").insert({"user_id": user_id, "count": 1}).execute()

    # Important: let the bot still process commands
    await bot.process_commands(message)

@bot.command()
async def activity(ctx, member: discord.Member = None):
    """
    !activity or !activity @user
    Shows how many messages a user has sent.
    """
    if member is None:
        member = ctx.author  # default to the command invoker

    user_id = str(member.id)
    data = supabase.table("user_activity").select("*").eq("user_id", user_id).execute()

    if data.data:
        count = data.data[0]["count"]
    else:
        count = 0

    await ctx.send(f"{member.mention} has sent **{count}** messages so far!")

@bot.command()
async def allactivity(ctx):
    """
    !allactivity
    Lists the message counts for all tracked users in descending order.
    """
    response = supabase.table("user_activity").select("*").execute()
    rows = response.data  # This is a list of dicts, each with { "user_id":..., "count": ... }

    if not rows:
        await ctx.send("No activity recorded yet.")
        return

    # Sort by count descending
    sorted_rows = sorted(rows, key=lambda x: x["count"], reverse=True)

    lines = []
    for row in sorted_rows:
        user_id = int(row["user_id"])  # convert back to int
        count = row["count"]
        member = ctx.guild.get_member(user_id)
        if member:
            lines.append(f"{member.display_name}: {count} messages")
        else:
            # user might not be in the guild or left
            lines.append(f"User ID {user_id}: {count} messages")

    # Limit how many results to display
    top_n = 20
    leaderboard = "\n".join(lines[:top_n])
    await ctx.send(f"**Activity Leaderboard**\n{leaderboard}")

###################################################################
#                   RUN THE BOT
###################################################################

if __name__ == "__main__":
    if not TOKEN:
        print("Error: BOT_TOKEN not found.")
    else:
        bot.run(TOKEN)
