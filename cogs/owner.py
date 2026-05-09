import discord
from discord.ext import commands
from datetime import datetime

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="noprefix", aliases=["np"], invoke_without_command=True)
    @commands.check(lambda ctx: ctx.author.id in ctx.bot.owner_ids)
    async def noprefix(self, ctx):
        embed = self.bot.crazy_embed(title="flaw • noprefix", description="manage users who can use commands without a prefix.")
        embed.add_field(name="⚙️ commands", value="`add <user>`, `remove <user>`, `list`", inline=False)
        await ctx.send(embed=embed)

    @noprefix.command(name="add", aliases=["a"])
    @commands.check(lambda ctx: ctx.author.id in ctx.bot.owner_ids)
    async def noprefix_add(self, ctx, user: discord.User):
        if user.id not in self.bot.noprefix_users:
            self.bot.noprefix_users.append(user.id)
            self.bot.save_noprefix()
            await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} **{user.name}** has been granted access."))
        else:
            await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} **{user.name}** is already in the list."))

    @noprefix.command(name="remove", aliases=["r", "rm", "del"])
    @commands.check(lambda ctx: ctx.author.id in ctx.bot.owner_ids)
    async def noprefix_remove(self, ctx, user: discord.User):
        if user.id in self.bot.noprefix_users:
            self.bot.noprefix_users.remove(user.id)
            self.bot.save_noprefix()
            await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} **{user.name}** has been removed."))
        else:
            await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} **{user.name}** was not in the list."))

    @noprefix.command(name="list", aliases=["l", "ls"])
    @commands.check(lambda ctx: ctx.author.id in ctx.bot.owner_ids)
    async def noprefix_list(self, ctx):
        if not self.bot.noprefix_users:
            return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} the list is empty."))
        
        users = []
        for i, u_id in enumerate(self.bot.noprefix_users, 1):
            try:
                user = await self.bot.fetch_user(u_id)
                users.append(f"`{i}.` **{user.name}** (`{u_id}`)")
            except:
                users.append(f"`{i}.` **unknown** (`{u_id}`)")
        
        embed = self.bot.crazy_embed(title="flaw • access list", description="\n".join(users))
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Owner(bot))
