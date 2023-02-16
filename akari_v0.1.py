import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import youtube_dl
import os
from dotenv import load_dotenv


load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

#intents = discord.Intents.default()
#intents.message_content = True

#client = discord.Client(intents=intents)

#bot = commands.Bot(command_prefix='/',intents=intents)
#bot = interactions.Client(token=DISCORD_TOKEN)


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sync(self, ctx) -> None:
        cmdno = await ctx.bot.tree.sync()
        await ctx.send(f"Synced {len(cmdno)} commands")
        return

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @app_commands.command(
        name="play",
        description="Akari plays a song - autosearch or URL"
    )
    @app_commands.describe(url="Youtube URL or song name (autosearch)")
    async def play(self, ctx, *, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f'Now playing: {player.title}')

    @app_commands.command(
        name="stop",
        description="Stops and disconnects Akari from voice chat"
    )
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description='Relatively simple music bot example',
    intents=intents,
)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


async def main():
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start(DISCORD_TOKEN)


asyncio.run(main())
