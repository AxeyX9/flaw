import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import json
import sqlite3
from colorama import Fore, Style, init
import sys
import time

# initialize colorama
init(autoreset=True)

# load env variables
load_dotenv()

# intents
intents = discord.Intents.all()

# config from env
BOT_CLIENT_ID = os.getenv("BOT_CLIENT_ID")
OWNER_IDS = [int(id.strip()) for id in os.getenv("OWNER_IDS", "").split(",") if id.strip().isdigit()]

class Database:
    def __init__(self, db_name="flaw.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup()

    def setup(self):
        # general guild settings
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS guilds (
            guild_id INTEGER PRIMARY KEY,
            prefix TEXT DEFAULT "'",
            log_channel_id INTEGER,
            welcome_channel_id INTEGER,
            welcome_message TEXT,
            autorole_id INTEGER,
            antinuke_enabled INTEGER DEFAULT 0,
            automod_enabled INTEGER DEFAULT 0,
            antilink_enabled INTEGER DEFAULT 0,
            antispam_enabled INTEGER DEFAULT 0
        )''')
        
        # Migrations: Add columns if they don't exist
        columns = [
            ("welcome_message", "TEXT"),
            ("antinuke_enabled", "INTEGER DEFAULT 0"),
            ("automod_enabled", "INTEGER DEFAULT 0"),
            ("antilink_enabled", "INTEGER DEFAULT 0"),
            ("antispam_enabled", "INTEGER DEFAULT 0")
        ]
        
        for col_name, col_type in columns:
            try:
                self.cursor.execute(f"ALTER TABLE guilds ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                # Column already exists
                pass

        # warnings
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            guild_id INTEGER,
            reason TEXT,
            moderator_id INTEGER,
            timestamp DATETIME
        )''')
        self.conn.commit()

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor

    def fetchone(self, query, params=()):
        return self.cursor.execute(query, params).fetchone()

    def fetchall(self, query, params=()):
        return self.cursor.execute(query, params).fetchall()

class FlawContext(commands.Context):
    async def send(self, content=None, **kwargs):
        if content:
            content = content.lower()
        
        if 'embed' in kwargs:
            embed = kwargs['embed']
            if embed.title: embed.title = embed.title.lower()
            if embed.description: embed.description = embed.description.lower()
            for field in embed.fields:
                field.name = field.name.lower()
                field.value = field.value.lower()
            if embed.footer.text: embed.footer.text = embed.footer.text.lower()
            if embed.author.name: embed.author.name = embed.author.name.lower()

        return await super().send(content, **kwargs)

class Flaw(commands.Bot):
    def __init__(self):
        def get_prefix(bot, message):
            if not message.guild:
                return "'"
            data = bot.db.fetchone("SELECT prefix FROM guilds WHERE guild_id = ?", (message.guild.id,))
            prefix = data[0] if data else "'"
            prefixes = [prefix]
            if message.author.id in bot.owner_ids or message.author.id in bot.noprefix_users:
                prefixes.append("")
            return prefixes

        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        self.db = Database()
        self.snipes = {}
        self.edit_snipes = {}
        self.afk_users = {}
        self.noprefix_users = self.load_noprefix()
        self.bot_client_id = BOT_CLIENT_ID
        self.owner_ids = OWNER_IDS
        self.uptime = datetime.utcnow()
        self.emojis_config = self.load_emojis()

    def load_emojis(self):
        if os.path.exists("emojis.json"):
            with open("emojis.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_emoji(self, name, default=""):
        return self.emojis_config.get(name, default)

    def get_emoji_obj(self, emoji_id: int):
        return discord.utils.get(self.emojis, id=emoji_id)

    def crazy_embed(self, title=None, description=None, color=0x2b2d31):
        embed = discord.Embed(
            description=description,
            color=color
        )
        if title:
            # Subtle lowercase title with thin styling
            embed.title = title.lower()
        
        if self.user:
            embed.set_footer(text=f"{self.user.name} • flawless automation", icon_url=self.user.display_avatar.url)
        return embed

    def load_noprefix(self):
        if os.path.exists("noprefix.json"):
            with open("noprefix.json", "r") as f:
                return json.load(f)
        return []

    def save_noprefix(self):
        with open("noprefix.json", "w") as f:
            json.dump(self.noprefix_users, f)

    async def get_context(self, message, *, cls=FlawContext):
        return await super().get_context(message, cls=cls)

    def log(self, category, message, color=Fore.WHITE):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.BLACK}{Style.BRIGHT}[{timestamp}] {color}{category.lower()} {Fore.WHITE}{message}")

    async def setup_hook(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}    flaw")
        print(f"{Fore.BLACK}{Style.BRIGHT}    the most addictive project\n")
        
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    self.log("cog", f"loaded {filename}", Fore.GREEN)
                except Exception as e:
                    self.log("error", f"failed {filename}: {e}", Fore.RED)

    async def on_ready(self):
        self.log("ready", f"logged in as {self.user}", Fore.MAGENTA)
        self.log("stats", f"guilds: {len(self.guilds)}", Fore.CYAN)
        activity = discord.CustomActivity(name="🔗 flaw.buzz")
        await self.change_presence(activity=activity)
        print("")

    async def on_message(self, message):
        if message.author.bot: return
        
        # jar style prefix mention response
        if self.user.mentioned_in(message) and len(message.content.split()) == 1:
            data = self.db.fetchone("SELECT prefix FROM guilds WHERE guild_id = ?", (message.guild.id,))
            prefix = data[0] if data else "'"
            embed = discord.Embed(
                description=f"{self.get_emoji('info')} {message.author.mention}: my prefix is `{prefix}`",
                color=0x7c4dff # purple-ish bar like ss
            )
            return await message.channel.send(embed=embed)

        if message.author.id in self.afk_users:
            data = self.afk_users.pop(message.author.id)
            time_passed = datetime.utcnow() - data['time']
            await message.channel.send(f"welcome back {message.author.mention}, you were afk for {int(time_passed.total_seconds())}s: {data['reason']}")
        
        for mention in message.mentions:
            if mention.id in self.afk_users:
                data = self.afk_users[mention.id]
                await message.channel.send(f"{mention.name} is afk: {data['reason']}")
                
        await self.process_commands(message)

    async def on_command(self, ctx):
        self.log("cmd", f"{ctx.author} used {ctx.command}", Fore.CYAN)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        embed = discord.Embed(color=0xff4b4b) # jar style red bar
        
        if isinstance(error, commands.MissingPermissions):
            embed.description = f"{self.get_emoji('error')} {ctx.author.mention}: you don't have the permissions to do that."
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"{self.get_emoji('error')} {ctx.author.mention}: you're missing a required argument: `{error.param.name}`"
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"{self.get_emoji('error')} {ctx.author.mention}: slow down. try again in `{error.retry_after:.2f}s`"
        elif isinstance(error, commands.MemberNotFound):
            embed.description = f"{self.get_emoji('error')} {ctx.author.mention}: i couldn't find that member."
        elif isinstance(error, commands.CheckFailure):
            embed.description = f"{self.get_emoji('error')} {ctx.author.mention}: you aren't allowed to use this command."
        else:
            embed.description = f"{self.get_emoji('error')} {ctx.author.mention}: something went wrong: `{str(error)}`"
            self.log("error", f"command error: {error}", Fore.RED)

        await ctx.send(embed=embed)

if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if token and token != "your_bot_token_here":
        bot = Flaw()
        bot.run(token)
    else:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.BLACK}{Style.BRIGHT}[{timestamp}] {Fore.RED}FATAL │ update the token in your .env file!")
