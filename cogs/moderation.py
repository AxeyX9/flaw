import discord
from discord.ext import commands
from datetime import datetime, timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick", aliases=["k"])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="no reason provided"):
        if ctx.author.top_role <= member.top_role:
            return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} {ctx.author.mention}: cannot target higher roles."))
        await member.kick(reason=reason)
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('hammer')} kicked **{member.name}** • `{reason}`"))

    @commands.command(name="ban", aliases=["b"])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="no reason provided"):
        if ctx.author.top_role <= member.top_role:
            return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} {ctx.author.mention}: cannot target higher roles."))
        await member.ban(reason=reason)
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('hammer')} banned **{member.name}** • `{reason}`"))

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member_id: int):
        try:
            user = await self.bot.fetch_user(member_id)
            await ctx.guild.unban(user)
            await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} unbanned **{user.name}**"))
        except discord.NotFound:
            await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} invalid user id."))

    @commands.command(name="timeout", aliases=["mute", "to", "shhh"])
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, minutes: int = 10, *, reason="no reason provided"):
        if ctx.author.top_role <= member.top_role:
            return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} {ctx.author.mention}: cannot target higher roles."))
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('timeout')} silenced **{member.name}** for `{minutes}m` • `{reason}`"))

    @commands.command(name="purge", aliases=["clear", "c"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10):
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('purge')} purged **{len(deleted)-1}** messages."), delete_after=3)

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason="no reason provided"):
        if ctx.author.top_role <= member.top_role:
            return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} {ctx.author.mention}: cannot target higher roles."))
        self.bot.db.execute("INSERT INTO warns (user_id, guild_id, reason, moderator_id, timestamp) VALUES (?, ?, ?, ?, ?)",
                            (member.id, ctx.guild.id, reason, ctx.author.id, datetime.utcnow()))
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('warning')} warned **{member.mention}** • `{reason}`"))

    @commands.command(name="warnings", aliases=["warns"])
    async def warnings(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        data = self.bot.db.fetchall("SELECT reason, moderator_id, timestamp FROM warns WHERE user_id = ? AND guild_id = ?", (member.id, ctx.guild.id))
        
        if not data:
            return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} | **{member.name} has no warnings**"))
        
        warn_list = []
        for i, (reason, mod_id, ts) in enumerate(data, 1):
            warn_list.append(f"**{i}.** {reason} (mod: <@{mod_id}>)")
        
        embed = self.bot.crazy_embed(title=f"warnings - {member.name}", description="\n".join(warn_list))
        await ctx.send(embed=embed)

    @commands.command(name="lockdown", aliases=["lock"])
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('lock')} | **locked {channel.mention}**"))

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('unlock')} | **unlocked {channel.mention}**"))

async def setup(bot):
    await bot.add_cog(Moderation(bot))
