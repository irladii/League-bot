import discord
from discord.ext import commands
import sqlite3
import threading
from flask import Flask, jsonify

TOKEN = "YOUR_DISCORD_BOT_TOKEN"
GUILD_ID = 1201768694972428318
ADMIN_ROLE_ID = 1201770467720175666
OWNER_ID = 229508905582067712

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="+", intents=intents)

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS teams(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shortcode TEXT UNIQUE,
            fullname TEXT,
            group_name TEXT,
            matches_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

def update_team(query, params):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def registerteam(ctx, shortcode, fullname, group):
    update_team("INSERT OR IGNORE INTO teams(shortcode, fullname, group_name) VALUES (?, ?, ?)",
                (shortcode, fullname, group.upper()))
    await ctx.send(f"✅ Registered **{fullname}** in Group **{group.upper()}**")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def registerwin(ctx, shortcode):
    update_team("""UPDATE teams
                   SET wins=wins+1, matches_played=matches_played+1, points=points+2
                   WHERE shortcode=?""", (shortcode,))
    await ctx.send(f"🏆 Win registered for `{shortcode}`")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def registerloss(ctx, shortcode):
    update_team("""UPDATE teams
                   SET losses=losses+1, matches_played=matches_played+1
                   WHERE shortcode=?""", (shortcode,))
    await ctx.send(f"💀 Loss registered for `{shortcode}`")

@bot.command()
async def resetdb(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ You don’t have permission. Get better 💀")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM teams")
    conn.commit()
    conn.close()
    await ctx.send("⚠️ Database reset.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("🚫 Not allowed. Get better 💀")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Missing arguments.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send("⚠️ Error occurred.")
        print(error)

# ---------------- Flask API ----------------
app = Flask(__name__)

def get_standings(group=None):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if group:
        cur.execute(
            "SELECT * FROM teams WHERE group_name=? ORDER BY points DESC, wins DESC, matches_played ASC",
            (group.upper(),))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {"group": group.upper(), "teams": rows}
    cur.execute(
        "SELECT * FROM teams ORDER BY group_name ASC, points DESC, wins DESC, matches_played ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"groups": rows}

@app.route("/standings")
def all_groups():
    return jsonify(get_standings())

@app.route("/standings/<group>")
def one_group(group):
    return jsonify(get_standings(group))

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# -------------------------------------------
if __name__ == "__main__":
    init_db()
    bot.run(TOKEN)
