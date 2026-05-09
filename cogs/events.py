import discord
from discord.ext import commands
from datetime import datetime

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def crazy_embed(self, title=None, description=None, color=0x2b2d31):
        embed = discord.Embed(
            description=description,
            color=color
        )
        if title:
            embed.title = title.lower()
        embed.set_footer(text="flaw", icon_url=self.bot.user.display_avatar.url)
        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # autorole
        data = self.bot.db.fetchone("SELECT autorole_id, welcome_channel_id FROM guilds WHERE guild_id = ?", (member.guild.id,))
        if data:
            role_id, welcome_id = data
            if role_id:
                role = member.guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
            
            if welcome_id:
                channel = member.guild.get_channel(welcome_id)
                if channel:
                    await channel.send(embed=self.crazy_embed(title="welcome", description=f"👋 | {member.mention} joined the server!"))

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return
        data = self.bot.db.fetchone("SELECT log_channel_id FROM guilds WHERE guild_id = ?", (message.guild.id,))
        if data and data[0]:
            channel = message.guild.get_channel(data[0])
            if channel:
                embed = self.crazy_embed(title="message deleted", description=f"**author:** {message.author.mention}\n**channel:** {message.channel.mention}\n**content:** {message.content}")
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Events(bot))
