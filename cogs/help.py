import discord
from discord.ext import commands
from datetime import datetime

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h", "cmds", "commands"])
    async def help(self, ctx):
        await ctx.reply("https://flaw.buzz/commands")

async def setup(bot):
    await bot.add_cog(Help(bot))
