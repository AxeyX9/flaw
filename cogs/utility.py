import discord
from discord.ext import commands
from datetime import datetime
import time

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", aliases=["latency", "ms"])
    async def ping(self, ctx):
        # WebSocket latency
        ws_latency = round(self.bot.latency * 1000)
        
        # REST API latency
        start = time.perf_counter()
        message = await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('satellite')} | **pinging...**"))
        end = time.perf_counter()
        rest_latency = round((end - start) * 1000)
        
        # Uptime
        uptime_delta = datetime.utcnow() - self.bot.uptime
        hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        description = (
            f"{self.bot.get_emoji('bolt')} **websocket:** `{ws_latency}ms`\n"
            f"{self.bot.get_emoji('broadcast')} **rest api:** `{rest_latency}ms`\n"
            f"{self.bot.get_emoji('hourglass')} **uptime:** `{uptime_str}`\n"
            f"{self.bot.get_emoji('globe')} **shard:** `{ctx.guild.shard_id if ctx.guild else 0}`"
        )
        
        await message.edit(embed=self.bot.crazy_embed(title="flaw • ping", description=description))

    @commands.command(name="invite", aliases=["inv"])
    async def invite(self, ctx):
        url = f"https://discord.com/oauth2/authorize?client_id={self.bot.bot_client_id}&permissions=8&scope=bot%20applications.commands"
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('link')} | [**invite flaw**]({url})"))

    @commands.command(name="afk", aliases=["away"])
    async def afk(self, ctx, *, reason="afk"):
        self.bot.afk_users[ctx.author.id] = {"reason": reason, "time": datetime.utcnow()}
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('sleep')} | {ctx.author.mention}: **{reason}**"))

    @commands.command(name="snipe", aliases=["s"])
    async def snipe(self, ctx):
        data = self.bot.snipes.get(ctx.channel.id)
        if not data: return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} | **nothing to snipe**"))
        embed = self.bot.crazy_embed(description=data['content'])
        embed.set_author(name=data['author'].name, icon_url=data['author'].display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="editsnipe", aliases=["es"])
    async def editsnipe(self, ctx):
        data = self.bot.edit_snipes.get(ctx.channel.id)
        if not data: return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} | **nothing to editsnipe**"))
        embed = self.bot.crazy_embed(description=f"**before:** {data['before']}\n**after:** {data['after']}")
        embed.set_author(name=data['author'].name, icon_url=data['author'].display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
