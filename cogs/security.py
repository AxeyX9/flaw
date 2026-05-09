import discord
from discord.ext import commands
import re

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="antinuke", aliases=["an"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def antinuke(self, ctx):
        """Configure the anti-nuke protection system."""
        data = self.bot.db.fetchone("SELECT antinuke_enabled FROM guilds WHERE guild_id = ?", (ctx.guild.id,))
        
        if not data or not data[0]:
            embed = self.bot.crazy_embed(
                title="flaw • antinuke",
                description=f"{self.bot.get_emoji('shield')} antinuke is currently **disabled**.\n\n`antinuke enable` to activate"
            )
            return await ctx.send(embed=embed)
            
        embed = self.bot.crazy_embed(
            title="flaw • antinuke",
            description=f"{self.bot.get_emoji('shield')} antinuke is currently **enabled**.\n\n`antinuke disable` to deactivate"
        )
        await ctx.send(embed=embed)

    @antinuke.command(name="enable", aliases=["on"])
    @commands.has_permissions(administrator=True)
    async def antinuke_enable(self, ctx):
        self.bot.db.execute("INSERT OR REPLACE INTO guilds (guild_id, antinuke_enabled) VALUES (?, 1)", (ctx.guild.id,))
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} antinuke protection has been **activated**."))

    @antinuke.command(name="disable", aliases=["off"])
    @commands.has_permissions(administrator=True)
    async def antinuke_disable(self, ctx):
        self.bot.db.execute("UPDATE guilds SET antinuke_enabled = 0 WHERE guild_id = ?", (ctx.guild.id,))
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} antinuke protection has been **deactivated**."))

    @commands.group(name="automod", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def automod(self, ctx):
        """Configure the automatic moderation system."""
        data = self.bot.db.fetchone("SELECT automod_enabled FROM guilds WHERE guild_id = ?", (ctx.guild.id,))
        
        if not data or not data[0]:
            embed = self.bot.crazy_embed(
                title="flaw • automod",
                description=f"{self.bot.get_emoji('mod')} automod is currently **disabled**."
            )
            return await ctx.send(embed=embed)

        embed = self.bot.crazy_embed(
            title="flaw • automod",
            description=f"{self.bot.get_emoji('mod')} automod is currently **enabled**."
        )
        await ctx.send(embed=embed)

    @commands.group(name="antilink", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def antilink(self, ctx):
        """Prevent users from posting links."""
        data = self.bot.db.fetchone("SELECT antilink_enabled FROM guilds WHERE guild_id = ?", (ctx.guild.id,))
        
        if not data or not data[0]:
            embed = self.bot.crazy_embed(
                title="flaw • antilink",
                description=f"{self.bot.get_emoji('link')} antilink is currently **disabled**.\n\n`antilink on` to enable"
            )
            return await ctx.send(embed=embed)
        
        embed = self.bot.crazy_embed(
            title="flaw • antilink",
            description=f"{self.bot.get_emoji('link')} antilink is currently **enabled**.\n\n`antilink off` to disable"
        )
        await ctx.send(embed=embed)

    @antilink.command(name="on", aliases=["enable"])
    @commands.has_permissions(manage_guild=True)
    async def antilink_on(self, ctx):
        self.bot.db.execute("INSERT OR REPLACE INTO guilds (guild_id, antilink_enabled) VALUES (?, 1)", (ctx.guild.id,))
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} antilink has been **enabled**."))

    @antilink.command(name="off", aliases=["disable"])
    @commands.has_permissions(manage_guild=True)
    async def antilink_off(self, ctx):
        self.bot.db.execute("UPDATE guilds SET antilink_enabled = 0 WHERE guild_id = ?", (ctx.guild.id,))
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} antilink has been **disabled**."))

    @commands.group(name="antispam", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def antispam(self, ctx):
        """Prevent users from spamming messages."""
        data = self.bot.db.fetchone("SELECT antispam_enabled FROM guilds WHERE guild_id = ?", (ctx.guild.id,))
        
        if not data or not data[0]:
            embed = self.bot.crazy_embed(
                title="flaw • antispam",
                description=f"{self.bot.get_emoji('warning')} antispam is currently **disabled**.\n\n`antispam on` to enable"
            )
            return await ctx.send(embed=embed)
        
        embed = self.bot.crazy_embed(
            title="flaw • antispam",
            description=f"{self.bot.get_emoji('warning')} antispam is currently **enabled**.\n\n`antispam off` to disable"
        )
        await ctx.send(embed=embed)

    @antispam.command(name="on", aliases=["enable"])
    @commands.has_permissions(manage_guild=True)
    async def antispam_on(self, ctx):
        self.bot.db.execute("INSERT OR REPLACE INTO guilds (guild_id, antispam_enabled) VALUES (?, 1)", (ctx.guild.id,))
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} antispam has been **enabled**."))

    @antispam.command(name="off", aliases=["disable"])
    @commands.has_permissions(manage_guild=True)
    async def antispam_off(self, ctx):
        self.bot.db.execute("UPDATE guilds SET antispam_enabled = 0 WHERE guild_id = ?", (ctx.guild.id,))
        await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} antispam has been **disabled**."))

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        data = self.bot.db.fetchone("SELECT antilink_enabled, antispam_enabled FROM guilds WHERE guild_id = ?", (message.guild.id,))
        if not data:
            return

        antilink, antispam = data

        # Antilink check
        if antilink and not message.author.guild_permissions.manage_messages:
            if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content):
                await message.delete()
                return await message.channel.send(f"{self.bot.get_emoji('error')} {message.author.mention}: links are not allowed here.", delete_after=3)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        data = self.bot.db.fetchone("SELECT antinuke_enabled FROM guilds WHERE guild_id = ?", (channel.guild.id,))
        if data and data[0]:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.user.id == channel.guild.owner_id:
                    return
                
                # Basic protection: ban the user who deleted the channel
                try:
                    await channel.guild.ban(entry.user, reason="antinuke: channel deletion")
                except:
                    pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        data = self.bot.db.fetchone("SELECT antinuke_enabled FROM guilds WHERE guild_id = ?", (role.guild.id,))
        if data and data[0]:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.user.id == role.guild.owner_id:
                    return
                
                try:
                    await role.guild.ban(entry.user, reason="antinuke: role deletion")
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Security(bot))
