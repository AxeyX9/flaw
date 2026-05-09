import discord
from discord.ext import commands
import re
import aiohttp
import io
import asyncio

class StealView(discord.ui.View):
    def __init__(self, bot, items, item_type="emoji"):
        super().__init__(timeout=60)
        self.bot = bot
        self.items = items # list of (url, name)
        self.item_type = item_type

    @discord.ui.button(label="Steal as Emoji", style=discord.ButtonStyle.blurple)
    async def steal_emoji(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check bot permissions
        if not interaction.guild.me.guild_permissions.manage_expressions:
             return await interaction.response.send_message(f"{self.bot.get_emoji('error')} | i need `manage emojis` permission to do this.", ephemeral=True)
             
        if not interaction.user.guild_permissions.manage_expressions:
            return await interaction.response.send_message("you need `manage emojis` permission.", ephemeral=True)
        
        await interaction.response.defer()
        
        async with aiohttp.ClientSession() as session:
            success_count = 0
            for url, name in self.items:
                async with session.get(url) as resp:
                    if resp.status != 200: continue
                    img = await resp.read()
                    try:
                        await interaction.guild.create_custom_emoji(name=name, image=img)
                        success_count += 1
                        # Wait 1 second for each emoji to prevent rate limits
                        await asyncio.sleep(1)
                    except discord.HTTPException as e:
                        if e.status == 429:
                            retry_after = e.retry_after if hasattr(e, 'retry_after') else "a while"
                            await interaction.followup.send(embed=self.bot.crazy_embed(
                                title="System Overload",
                                description=f"{self.bot.get_emoji('error')} | **Discord Rate Limit Triggered.**\n{self.bot.get_emoji('hourglass')} **Retry in:** `{retry_after}` seconds.\n\n*Aborting remaining items to prevent further lock.*"
                            ))
                            break
                        else:
                            await interaction.followup.send(f"failed to steal {name}: {e}", ephemeral=True)
                            continue
                    except Exception as e:
                        await interaction.followup.send(f"failed to steal {name}: {e}", ephemeral=True)
                        continue

        if success_count > 0:
            await interaction.followup.send(f"{self.bot.get_emoji('success')} successfully stolen {success_count} emoji(s).")
        self.stop()

    @discord.ui.button(label="Steal as Sticker", style=discord.ButtonStyle.green)
    async def steal_sticker(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_expressions:
            return await interaction.response.send_message("you need `manage stickers` permission.", ephemeral=True)
        
        if len(self.items) > 1:
            return await interaction.response.send_message("can only steal 1 sticker at a time.", ephemeral=True)

        await interaction.response.defer()
        url, name = self.items[0]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    img = await resp.read()
                    file = discord.File(io.BytesIO(img), filename=f"{name}.png")
                    try:
                        await interaction.guild.create_sticker(name=name, description="stolen via flaw", emoji="😎", file=file)
                        await interaction.followup.send(f"{self.bot.get_emoji('success')} successfully stolen sticker.")
                    except discord.HTTPException as e:
                        if e.status == 429:
                            retry_after = e.retry_after if hasattr(e, 'retry_after') else "a while"
                            await interaction.followup.send(embed=self.bot.crazy_embed(
                                title="System Overload",
                                description=f"{self.bot.get_emoji('error')} | **Discord Rate Limit Triggered (Sticker).**\n{self.bot.get_emoji('hourglass')} **Retry in:** `{retry_after}` seconds."
                            ))
                        else:
                            await interaction.followup.send(f"failed to steal sticker: {e}", ephemeral=True)
                    except Exception as e:
                        await interaction.followup.send(f"failed to steal sticker: {e}", ephemeral=True)
        self.stop()

class Emoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="steal", aliases=["addemoji", "clone"])
    @commands.has_permissions(manage_expressions=True)
    async def steal(self, ctx, *, reference: str = None):
        """Steals emojis or stickers from a message or attachment."""
        items = []
        
        # 1. Check for attachments in the current message
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']):
                    items.append((attachment.url, attachment.filename.split('.')[0]))

        # 2. Check for reply
        target = None
        if ctx.message.reference:
            try:
                target = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except:
                pass
        
        if target:
            # Check target attachments
            if target.attachments:
                for attachment in target.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']):
                        items.append((attachment.url, attachment.filename.split('.')[0]))
            
            # Check target stickers
            if target.stickers:
                for sticker in target.stickers:
                    items.append((sticker.url, sticker.name))
            
            # Check target content
            if target.content:
                custom_emojis = re.findall(r'<(a?):(\w+):(\d+)>', target.content)
                for animated, name, emoji_id in custom_emojis:
                    ext = "gif" if animated else "png"
                    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"
                    items.append((url, name))

        # 3. Check reference/args content
        if reference:
            # Match custom emojis in args
            custom_emojis = re.findall(r'<(a?):(\w+):(\d+)>', reference)
            for animated, name, emoji_id in custom_emojis:
                ext = "gif" if animated else "png"
                url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"
                items.append((url, name))
            
            # Check if reference is a direct image URL
            if reference.startswith("http") and any(reference.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']):
                name = reference.split('/')[-1].split('?')[0].split('.')[0]
                items.append((reference, name or "stolen_emoji"))

        # Remove duplicates
        unique_items = []
        seen_urls = set()
        for url, name in items:
            if url not in seen_urls:
                unique_items.append((url, name))
                seen_urls.add(url)

        if not unique_items:
            return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} | no emojis, stickers, or images found to steal. try replying to a message or providing a link/emoji."))

        embed = self.bot.crazy_embed(
            title="Choose what to steal:",
            description=f"detected **{len(unique_items)}** item(s)."
        )
        
        if len(unique_items) == 1:
            embed.set_image(url=unique_items[0][0])
        
        view = StealView(self.bot, unique_items)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="emojis", aliases=["emojilist", "el"])
    async def emojis(self, ctx):
        """Lists all custom emojis mapped in the bot's configuration."""
        description = ""
        for name, emoji_str in self.bot.emojis_config.items():
            # Filter out the long functional names for a cleaner list
            if len(description) > 1800:
                break
            description += f"{emoji_str} `{name}` "
        
        embed = self.bot.crazy_embed(
            title="flaw emojis",
            description=description or "No emojis mapped yet."
        )
        await ctx.send(embed=embed)

    @commands.command(name="badges", aliases=["status", "roles"])
    async def badges(self, ctx, member: discord.Member = None):
        """Displays a user's badges based on their roles and status."""
        member = member or ctx.author
        badges = []

        # Mapping roles/status to custom emojis
        if member.id in self.bot.owner_ids:
            badges.append(f"{self.bot.get_emoji('owner')} **Owner**")
        
        if member.guild_permissions.administrator:
            badges.append(f"{self.bot.get_emoji('administrator')} **Admin**")
        
        # Check for specific role names or permissions
        role_names = [role.name.lower() for role in member.roles]
        
        if "staff" in role_names:
            badges.append(f"{self.bot.get_emoji('staff')} **Staff**")
        if "developer" in role_names:
            badges.append(f"{self.bot.get_emoji('developer')} **Developer**")
        if "designer" in role_names:
            badges.append(f"{self.bot.get_emoji('designer')} **Designer**")
        if "verified" in role_names or member.bot:
            badges.append(f"{self.bot.get_emoji('verified')} **Verified**")
        if member.premium_since:
            badges.append(f"{self.bot.get_emoji('booster')} **Booster**")
        
        # Default badge if nothing else
        if not badges:
            badges.append(f"{self.bot.get_emoji('member')} **Member**")

        description = "\n".join(badges)
        embed = self.bot.crazy_embed(
            title=f"flaw • {member.name}",
            description=description
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="emojify")
    async def emojify(self, ctx, *, text: str):
        """Converts text into big emoji letters."""
        emojified = ""
        for char in text.lower():
            if char.isalpha():
                emojified += f":regional_indicator_{char}: "
            elif char.isdigit():
                numbers = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
                emojified += f":{numbers[int(char)]}: "
            else:
                emojified += char
        
        if len(emojified) > 2000:
            return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} | Text is too long to emojify."))
        
        await ctx.send(emojified)

    @commands.command(name="react")
    @commands.has_permissions(add_reactions=True)
    async def react(self, ctx, message_id: int, emoji_name: str):
        """Reacts to a message using a custom emoji from the config."""
        try:
            message = await ctx.channel.fetch_message(message_id)
            emoji = self.bot.get_emoji(emoji_name.lower())
            
            if not emoji:
                return await ctx.send(embed=self.bot.crazy_embed(
                    description=f"{self.bot.get_emoji('error')} | Emoji `{emoji_name}` not found in configuration."
                ))

            # Extract the actual emoji ID from the custom emoji string
            # Format: <:name:id> or <a:name:id>
            if ":" in emoji:
                emoji_id = int(emoji.split(":")[-1].replace(">", ""))
                actual_emoji = self.bot.get_emoji_obj(emoji_id) # Need to add this helper
                if not actual_emoji:
                    # Fallback to string if object not found (might be from another server)
                    await message.add_reaction(emoji)
                else:
                    await message.add_reaction(actual_emoji)
            else:
                await message.add_reaction(emoji)
                
            await ctx.message.add_reaction(self.bot.get_emoji("success"))
            
        except discord.NotFound:
            await ctx.send(embed=self.bot.crazy_embed(
                description=f"{self.bot.get_emoji('error')} | Message ID `{message_id}` not found in this channel."
            ))
        except Exception as e:
            await ctx.send(embed=self.bot.crazy_embed(
                description=f"{self.bot.get_emoji('error')} | Failed to react: `{str(e)}`"
            ))

async def setup(bot):
    await bot.add_cog(Emoji(bot))
