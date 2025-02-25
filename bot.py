import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from supabase import create_client, Client

# -----------------------------------------------------------------------------
# 1. Load environment variables from .env
# -----------------------------------------------------------------------------
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")              # Discord bot token
SUPABASE_URL = os.getenv("SUPABASE_URL")    # e.g. "https://abccompany.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # or use SERVICE_ROLE_KEY if needed

# -----------------------------------------------------------------------------
# 2. Create Supabase client
# -----------------------------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------------------------------------------------------
# 3. Set up Discord Intents
# -----------------------------------------------------------------------------
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Needed to read message content

# -----------------------------------------------------------------------------
# 4. Create the Bot
# -----------------------------------------------------------------------------
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------------------------------------------------------
# EVENTS
# -----------------------------------------------------------------------------

@bot.event
async def on_ready():
    """
    Called when the bot has successfully connected to Discord.
    Prints the bot's user info to confirm everything is working.
    """
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message):
    """
    Tracks user messages in Supabase. Whenever a user (not the bot itself)
    sends a message, we increment their count in the DB.

    We store only the user's Discord ID in the database, which is permanent
    and never changes, ensuring a reliable way to track them.
    """
    if message.author == bot.user:
        return

    user_id = str(message.author.id)

    # Fetch existing record
    data = supabase.table("user_activity").select("*").eq("user_id", user_id).execute()

    if data.data:
        current_count = data.data[0]["count"]
        supabase.table("user_activity") \
                .update({"count": current_count + 1}) \
                .eq("user_id", user_id) \
                .execute()
    else:
        supabase.table("user_activity") \
                .insert({"user_id": user_id, "count": 1}) \
                .execute()

    await bot.process_commands(message)

# -----------------------------------------------------------------------------
# COMMANDS
# -----------------------------------------------------------------------------

@bot.command()
async def activity(ctx, *, user_input: str = None):
    """
    Command: !activity [user_input]
    Shows how many messages a user has sent. If no user_input is given,
    it defaults to the command caller (ctx.author).

    user_input can be:
    - A mention (e.g., @User)
    - A user ID (e.g., 123456789012345678)
    - An exact username or display name (case-insensitive).
    """
    # 1. If no user_input is provided, show the author's activity
    if not user_input:
        target_user = ctx.author
    else:
        # We'll try mention -> ID -> exact name or display name.
        target_user = None

        # Step A: Strip possible mention characters <@! ... >
        mention_id = user_input.strip("<@!>")
        if mention_id.isdigit():
            target_user = ctx.guild.get_member(int(mention_id))

        # Step B: If not found yet, try if it's just a numeric ID
        if not target_user and user_input.isdigit():
            target_user = ctx.guild.get_member(int(user_input))

        # Step C: If still not found, try matching username or display name exactly (case-insensitive)
        if not target_user:
            # Lowercase the input for comparison
            user_input_lower = user_input.lower()

            # Gather possible matches
            matched_members = [
                m for m in ctx.guild.members
                if m.name.lower() == user_input_lower
                or m.display_name.lower() == user_input_lower
            ]

            if len(matched_members) == 1:
                target_user = matched_members[0]
            elif len(matched_members) > 1:
                await ctx.send(
                    "Found **multiple** users with that name. "
                    "Please mention the exact user or use their ID."
                )
                return

        # Final check: if we still don't have a user, fail gracefully
        if not target_user:
            await ctx.send("Could not find a user with that name, mention, or ID.")
            return

    # 2. Now we have a valid Discord user object
    user_id = str(target_user.id)
    data = supabase.table("user_activity").select("*").eq("user_id", user_id).execute()
    count = data.data[0]["count"] if data.data else 0

    await ctx.send(f"{target_user.mention} has sent **{count}** messages so far!")


@bot.command()
async def allactivity(ctx):
    """
    Command: !allactivity
    Lists message counts for all tracked users in descending order.
    Dynamically fetches user display names from the Discord API to ensure
    they are always current.
    """
    response = supabase.table("user_activity").select("*").execute()
    rows = response.data  # A list of dicts, e.g. [{ "user_id": "123", "count": 4 }, ...]

    if not rows:
        await ctx.send("No activity recorded yet.")
        return

    # Sort by 'count' descending
    sorted_rows = sorted(rows, key=lambda x: x["count"], reverse=True)

    lines = []
    for row in sorted_rows:
        user_id_int = int(row["user_id"])
        count = row["count"]

        member = ctx.guild.get_member(user_id_int)
        if member:
            lines.append(f"{member.display_name}: {count} messages")
        else:
            # If the user isn't in the guild, fallback to "User ID"
            lines.append(f"User ID {user_id_int}: {count} messages")

    # Limit results to the top 20
    top_n = 20
    leaderboard = "\n".join(lines[:top_n])

    await ctx.send(f"**Activity Leaderboard**\n{leaderboard}")

# -----------------------------------------------------------------------------
# RUN THE BOT
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    if not TOKEN:
        print("Error: BOT_TOKEN not found in environment variables.")
    else:
        bot.run(TOKEN)
