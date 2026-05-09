import discord
from discord.ext import commands

class Welcomer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="welcomer", aliases=["welcome"], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def welcomer(self, ctx):
        """Configure the welcome system."""
        data = self.bot.db.fetchone("SELECT welcome_channel_id, welcome_message FROM guilds WHERE guild_id = ?", (ctx.guild.id,))
        channel_id = data[0] if data else None
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        
        embed = self.bot.crazy_embed(
            title="flaw • welcomer",
            description=(
                f"{self.bot.get_emoji('rocket')} **channel:** {channel.mention if channel else 'not set'}\n"
                f"{self.bot.get_emoji('notes')} **message:** `{data[1] if data and data[1] else 'default'}`\n\n"
                "`welcomer channel <#channel>` to set destination\n"
                "`welcomer message <text>` to customize text\n"
                "`welcomer test` to preview"
            )
        )
        await ctx.send(embed=embed)

    @welcomer.command(name="channel")
    @commands.has_permissions(manage_guild=True)
    async def welcomer_channel(self, ctx, channel: discord.TextChannel):
        self.bot.db.execute("INSERT OR REPLACE INTO guilds (guild_id, welcome_channel_id) VALUES (?, ?)", (ctx.guild.id, channel.id))
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} welcome messages will now be sent to {channel.mention}."))

    @welcomer.command(name="message")
    @commands.has_permissions(manage_guild=True)
    async def welcomer_message(self, ctx, *, message: str):
        self.bot.db.execute("UPDATE guilds SET welcome_message = ? WHERE guild_id = ?", (message, ctx.guild.id))
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} welcome message updated successfully."))

    @welcomer.command(name="test")
    @commands.has_permissions(manage_guild=True)
    async def welcomer_test(self, ctx):
        data = self.bot.db.fetchone("SELECT welcome_channel_id, welcome_message FROM guilds WHERE guild_id = ?", (ctx.guild.id,))
        if not data or not data[0]:
            return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} setup a channel first using `welcomer channel`."))
        
        channel = ctx.guild.get_channel(data[0])
        msg = data[1] or "welcome to the server, {user}!"
        msg = msg.replace("{user}", ctx.author.mention).replace("{guild}", ctx.guild.name)
        
        await channel.send(msg)
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} test message sent to {channel.mention}."))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = self.bot.db.fetchone("SELECT welcome_channel_id, welcome_message FROM guilds WHERE guild_id = ?", (member.guild.id,))
        if not data or not data[0]:
            return
        
        channel = member.guild.get_channel(data[0])
        if not channel:
            return
            
        msg = data[1] or "welcome to the server, {user}!"
        msg = msg.replace("{user}", member.mention).replace("{guild}", member.guild.name)
        
        try:
            await channel.send(msg)
        except:
            pass

async def setup(bot):
    await bot.add_cog(Welcomer(bot))
