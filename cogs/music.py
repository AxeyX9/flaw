import discord
from discord.ext import commands
import yt_dlp
import asyncio
from datetime import datetime
import collections

# ytdl options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class MusicView(discord.ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=None)
        self.cog = cog
        self.ctx = ctx

    @discord.ui.button(emoji="<:backwards:1502560462082932796>", style=discord.ButtonStyle.gray)
    async def backward(self, interaction: discord.Interaction, button: discord.ui.Button):
        # rewind logic if supported, for now just placeholder
        await interaction.response.send_message("rewinding...", ephemeral=True)

    @discord.ui.button(emoji="<:notes:1502560506265862154>", style=discord.ButtonStyle.gray)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != interaction.guild.voice_client.channel:
            return await interaction.response.send_message("join the vc first", ephemeral=True)
        
        self.cog.loops[interaction.guild.id] = not self.cog.loops.get(interaction.guild.id, False)
        status = "enabled" if self.cog.loops[interaction.guild.id] else "disabled"
        await interaction.response.send_message(f"loop {status}", ephemeral=True)

    @discord.ui.button(emoji="<:pause:1428599118086930473>", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != interaction.guild.voice_client.channel:
            return await interaction.response.send_message("join the vc first", ephemeral=True)
        
        vc = interaction.guild.voice_client
        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message(f"{self.cog.bot.get_emoji('success')} paused", ephemeral=True)

    @discord.ui.button(emoji="<:play:1428600313350324234>", style=discord.ButtonStyle.gray)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != interaction.guild.voice_client.channel:
            return await interaction.response.send_message("join the vc first", ephemeral=True)
        
        vc = interaction.guild.voice_client
        if vc.is_paused():
            vc.resume()
            await interaction.response.send_message(f"{self.cog.bot.get_emoji('success')} resumed", ephemeral=True)

    @discord.ui.button(emoji="<:queue:1502560514956464208>", style=discord.ButtonStyle.gray)
    async def queue_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        queue = self.cog.queues.get(interaction.guild.id, [])
        if not queue:
            return await interaction.response.send_message(f"{self.cog.bot.get_emoji('error')} queue is empty", ephemeral=True)
        
        description = "\n".join([f"{self.cog.bot.get_emoji('notes')} `{i+1}.` {song.title}" for i, song in enumerate(queue[:10])])
        embed = self.cog.bot.crazy_embed(title="sonic queue", description=description)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(emoji="<:forwards:1502560470245052507>", style=discord.ButtonStyle.gray)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != interaction.guild.voice_client.channel:
            return await interaction.response.send_message("join the vc first", ephemeral=True)
        
        vc = interaction.guild.voice_client
        vc.stop()
        await interaction.response.send_message(f"{self.cog.bot.get_emoji('success')} skipped", ephemeral=True)

    @discord.ui.button(emoji="<:stop:1428601342825336843>", style=discord.ButtonStyle.danger)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or interaction.user.voice.channel != interaction.guild.voice_client.channel:
            return await interaction.response.send_message("join the vc first", ephemeral=True)
        
        vc = interaction.guild.voice_client
        self.cog.queues[interaction.guild.id].clear()
        vc.stop()
        await vc.disconnect()
        await interaction.response.send_message(f"{self.cog.bot.get_emoji('success')} stopped and cleared", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = collections.defaultdict(list)
        self.loops = collections.defaultdict(bool)

    def error_embed(self, ctx, message):
        return discord.Embed(description=f"{self.bot.get_emoji('error')} {ctx.author.mention}: {message}", color=0xff4b4b)

    def play_next(self, ctx):
        if self.loops[ctx.guild.id] and ctx.voice_client.source:
            # this is tricky with discord.py, usually you'd re-create the source
            # for now, let's handle standard queueing
            pass

        if self.queues[ctx.guild.id]:
            next_song = self.queues[ctx.guild.id].pop(0)
            ctx.voice_client.play(next_song, after=lambda e: self.play_next(ctx))
            asyncio.run_coroutine_threadsafe(self.send_play_embed(ctx, next_song), self.bot.loop)

    async def send_play_embed(self, ctx, player):
        minutes, seconds = divmod(player.duration, 60)
        duration_str = f"{int(minutes):02d}:{int(seconds):02d}"
        
        # ultra-clean status line
        dots = f"{self.bot.get_emoji('status_online')} **playing** • {duration_str}"
        
        embed = self.bot.crazy_embed(
            title="flaw music",
            description=f"{self.bot.get_emoji('music')} **[{player.title}]({player.url})**\n{dots}"
        )
        embed.set_thumbnail(url=player.thumbnail)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        
        view = MusicView(self, ctx)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="play", aliases=["p", "stream", "add"])
    async def play(self, ctx, *, url: str):
        if not ctx.author.voice:
            return await ctx.send(embed=self.error_embed(ctx, "join a vc first"))
        
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                if ctx.voice_client.is_playing():
                    self.queues[ctx.guild.id].append(player)
                    return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('success')} | added **{player.title}** to the sonic queue"))
                
                ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
                await self.send_play_embed(ctx, player)
            except Exception as e:
                await ctx.send(embed=self.error_embed(ctx, f"error: `{str(e)}`"))

    @commands.command(name="stop", aliases=["leave", "dc"])
    async def stop(self, ctx):
        if ctx.voice_client:
            self.queues[ctx.guild.id].clear()
            await ctx.voice_client.disconnect()
            await ctx.send(embed=self.bot.crazy_embed(description=f"👋 | **disconnected.** session cleared."))

    @commands.command(name="skip", aliases=["sk", "skp"])
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('skip')} | **skipped.** moving to next track..."))

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        queue = self.queues.get(ctx.guild.id, [])
        if not queue: return await ctx.send(embed=self.bot.crazy_embed(description=f"{self.bot.get_emoji('error')} | **the queue is currently empty.**"))
        
        description = "\n".join([f"`{i+1}.` {song.title}" for i, song in enumerate(queue[:10])])
        if len(queue) > 10:
            description += f"\n... and `{len(queue)-10}` more"
            
        await ctx.send(embed=self.bot.crazy_embed(title="sonic queue", description=description))

    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume(self, ctx, volume: int):
        if not ctx.voice_client: return
        if not 0 <= volume <= 200: return await ctx.send(embed=self.error_embed(ctx, "0-200 only"))
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(embed=self.bot.crazy_embed(description=f"🔊 | **volume: {volume}%**"))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.guild.voice_client:
            return

        # check if the bot is now alone in the channel
        voice_channel = member.guild.voice_client.channel
        if len(voice_channel.members) == 1: # only the bot is left
            self.queues[member.guild.id].clear()
            await member.guild.voice_client.disconnect()
            
            # optional: log to terminal
            self.bot.log("music", f"auto-left {voice_channel.name} (channel empty)", Fore.YELLOW)

async def setup(bot):
    await bot.add_cog(Music(bot))
