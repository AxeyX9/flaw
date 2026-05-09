import discord
from discord.ext import commands
from datetime import datetime

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo", aliases=["ui", "whois", "user", "u"])
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        roles = [role.mention for role in reversed(member.roles[1:])]
        
        description = (
            f"{self.bot.get_emoji('user')} {member.mention}\n"
            f"{self.bot.get_emoji('id')} `{member.id}`\n\n"
            f"**joined**\n"
            f"<t:{int(member.created_at.timestamp())}:R> (discord)\n"
            f"<t:{int(member.joined_at.timestamp())}:R> (server)\n\n"
            f"**roles [{len(roles)}]**\n"
            f"{' '.join(roles[:5])}{' ...' if len(roles) > 5 else '' if roles else 'none'}"
        )
        
        embed = self.bot.crazy_embed(title="user analytics", description=description)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="avatar", aliases=["av", "pfp", "icon"])
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = self.bot.crazy_embed(title="visual identity", description=f"{self.bot.get_emoji('link')} [**download**]({member.display_avatar.url})")
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["si", "server", "guild"])
    async def serverinfo(self, ctx):
        guild = ctx.guild
        description = (
            f"{self.bot.get_emoji('crown')} {guild.owner.mention}\n"
            f"{self.bot.get_emoji('id')} `{guild.id}`\n\n"
            f"**metrics**\n"
            f"{self.bot.get_emoji('members')} `{guild.member_count:,}` members\n"
            f"{self.bot.get_emoji('gem')} level `{guild.premium_tier}` ({guild.premium_subscription_count} boosts)\n"
            f"{self.bot.get_emoji('folder')} `{len(guild.channels)}` channels\n\n"
            f"**created**\n"
            f"<t:{int(guild.created_at.timestamp())}:D> (<t:{int(guild.created_at.timestamp())}:R>)"
        )
        embed = self.bot.crazy_embed(title="guild analytics", description=description)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
