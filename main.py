import discord
from discord.ext import commands
import sqlite3
import asyncio

TOKEN = "YOUR_DISCORD_BOT_TOKEN"  # Replace with your actual bot token
GUILD_ID = 1201768694972428318
ADMIN_ROLE_ID = 1201770467720175666
OWNER_ID = 229508905582067712

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='+', intents=intents)

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shortcode TEXT UNIQUE,
                fullname TEXT,
                group_name TEXT,
                matches_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0
            )""")
    conn.commit()
    conn.close()

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

async def add_team(shortcode, fullname, group_name):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO teams (shortcode, fullname, group_name) VALUES (?, ?, ?)", 
              (shortcode, fullname, group_name))
    conn.commit()
    conn.close()

async def register_win(shortcode):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE teams SET wins = wins + 1, matches_played = matches_played + 1, points = points + 2 WHERE shortcode = ?", (shortcode,))
    conn.commit()
    conn.close()

async def register_loss(shortcode):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE teams SET losses = losses + 1, matches_played = matches_played + 1 WHERE shortcode = ?", (shortcode,))
    conn.commit()
    conn.close()

@bot.command(name="registerteam")
@commands.has_role(ADMIN_ROLE_ID)
async def register_team(ctx, shortcode: str, fullname: str, group: str):
    await add_team(shortcode, fullname, group)
    await ctx.send(f"✅ Team **{fullname}** registered under group **{group}**")

@bot.command(name="registerwin")
@commands.has_role(ADMIN_ROLE_ID)
async def reg_win(ctx, shortcode: str):
    await register_win(shortcode)
    await ctx.send(f"🏆 Win registered for team `{shortcode}`")

@bot.command(name="registerloss")
@commands.has_role(ADMIN_ROLE_ID)
async def reg_loss(ctx, shortcode: str):
    await register_loss(shortcode)
    await ctx.send(f"💀 Loss registered for team `{shortcode}`")

@bot.command(name="resetdb")
async def reset_db(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ You don’t have permission for this command. Get better 💀")
        return
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM teams")
    conn.commit()
    conn.close()
    await ctx.send("⚠️ Database has been reset by the owner.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("🚫 You’re not allowed to use this command. Get better 💀")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Missing argument! Please check your command usage.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send("⚠️ Unexpected error occurred.")
        print(f"Error: {error}")

if __name__ == "__main__":
    init_db()
    bot.run(TOKEN)
