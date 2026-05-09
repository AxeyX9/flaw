import discord
from discord.ext import commands
from datetime import datetime

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setprefix")
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, prefix: str):
        self.bot.db.execute("INSERT OR REPLACE INTO guilds (guild_id, prefix) VALUES (?, ?)", (ctx.guild.id, prefix))
        await ctx.send(embed=self.bot.crazy_embed(title="flaw • prefix", description=f"{self.bot.get_emoji('success')} server prefix set to `{prefix}`"))

    @commands.command(name="setlogs")
    @commands.has_permissions(administrator=True)
    async def setlogs(self, ctx, channel: discord.TextChannel):
        self.bot.db.execute("UPDATE guilds SET log_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
        await ctx.send(embed=self.bot.crazy_embed(title="flaw • logging", description=f"{self.bot.get_emoji('success')} log stream directed to {channel.mention}"))

    @commands.command(name="setwelcome")
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx, channel: discord.TextChannel):
        self.bot.db.execute("UPDATE guilds SET welcome_channel_id = ? WHERE guild_id = ?", (channel.id, ctx.guild.id))
        await ctx.send(embed=self.bot.crazy_embed(title="flaw • entry", description=f"{self.bot.get_emoji('success')} welcoming protocols set in {channel.mention}"))

    @commands.command(name="setautorole")
    @commands.has_permissions(administrator=True)
    async def setautorole(self, ctx, role: discord.Role):
        self.bot.db.execute("UPDATE guilds SET autorole_id = ? WHERE guild_id = ?", (role.id, ctx.guild.id))
        await ctx.send(embed=self.bot.crazy_embed(title="flaw • roles", description=f"{self.bot.get_emoji('success')} auto-role set to **{role.name}**"))

async def setup(bot):
    await bot.add_cog(Config(bot))
