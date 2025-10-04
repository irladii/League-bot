import os
import threading
import sqlite3
from flask import Flask, jsonify
import discord
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("No DISCORD_TOKEN found in environment variables. Add it in Replit Secrets.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="+", intents=intents)

# Database setup
DB_FILE = "league.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shortcode TEXT UNIQUE,
                    name TEXT,
                    group_id TEXT,
                    played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    points INTEGER DEFAULT 0
                )''')
    conn.commit()
    conn.close()

init_db()

# Bot commands
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def registerteam(ctx, shortcode: str, *, full_name_and_group: str):
    try:
        parts = full_name_and_group.split()
        full_name = " ".join(parts[:-1])
        group = parts[-1].upper()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO teams (shortcode, name, group_id) VALUES (?, ?, ?)", (shortcode.upper(), full_name, group))
        conn.commit()
        conn.close()

        await ctx.send(f"✅ Registered team {full_name} ({shortcode.upper()}) in Group {group}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def registerwin(ctx, shortcode: str):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM teams WHERE shortcode=?", (shortcode.upper(),))
        team = c.fetchone()
        if not team:
            await ctx.send("❌ Team not found.")
            return
        c.execute("UPDATE teams SET played=played+1, wins=wins+1, points=points+2 WHERE shortcode=?", (shortcode.upper(),))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Win registered for {shortcode.upper()}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def registerloss(ctx, shortcode: str):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM teams WHERE shortcode=?", (shortcode.upper(),))
        team = c.fetchone()
        if not team:
            await ctx.send("❌ Team not found.")
            return
        c.execute("UPDATE teams SET played=played+1, losses=losses+1 WHERE shortcode=?", (shortcode.upper(),))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Loss registered for {shortcode.upper()}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def resetdb(ctx):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM teams")
        conn.commit()
        conn.close()
        await ctx.send("✅ Database reset.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# Flask API
app = Flask(__name__)

@app.route("/api/standings/<group>")
def api_standings(group):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, played, wins, losses, points FROM teams WHERE group_id=?", (group.upper(),))
    rows = c.fetchall()
    conn.close()
    result = [{"name": r[0], "played": r[1], "wins": r[2], "losses": r[3], "points": r[4]} for r in rows]
    return jsonify(result)

def run_api():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=run_api).start()
    bot.run(DISCORD_TOKEN)
