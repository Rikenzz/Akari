import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import youtube_dl
import os
from dotenv import load_dotenv


# YoutubeDL config
youtube_dl.utils.bug_reports_message = lambda: ''

# Create a list to store the music queue
queue = []

# Function to play music
async def play_song(ctx, url):
    def check_queue():
        if queue:
            next_song= queue[0]
            queue.pop(0)
            play_song(ctx, next_song)

    # Get the voice client for the bot's current server
    voice_client = ctx.guild.voice_client

    # Create a youtube-dl player and start playing the song
    ytdl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': False,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'ffmpeg_options': {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
    }
    with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
        info = ytdl.extract_info(url, download=False)
        URL = info['formats'][0]['url']
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(URL, **ytdl_opts['ffmpeg_options']))
        voice_client.play(source, after=lambda e: check_queue())

    # Send a message to the channel indicating the song is playing
    song_title = info['title']
    await ctx.send(f'Now playing: {song_title}')

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def sync(self, ctx) -> None:
        cmdno = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(cmdno)} commands")
        return
    

    # PLAY
    @app_commands.command(
        name="play",
        description="Play a song"
    )
    @app_commands.describe(song="Youtube URL or song name (autosearch)")
    async def play(self, ctx, song: str):
        # Check if user is in a voice channel
        if not ctx.author.voice:
            await ctx.send('You are not connected to a voice channel.')
            return
        
        # Get voice client for current server
        voice_client = ctx.guild.voice_client

        # Check if bot is already playing music
        if voice_client and voice_client.is_playing():
            queue.append(song)
            await ctx.send(f'{song} has been added to the queue.')
        else:
            # Connect bot to user's voice channel
            channel = ctx.author.voice.channel
            await channel.connect()

            # Play the song
            await play_song(ctx, song)


    # SKIP
    @app_commands.command(
        name="skip",
        description="Skip current song"
    )
    async def skip(self, ctx):
        # Get voice client for current server
        voice_client = ctx.guild.voice_client

        # Check if the bot is playing music
        if not voice_client or not voice_client.is_playing():
            await ctx.send('The bot is not playing any music.')
            return

        # Stop playing the current song
        voice_client.stop()


    # STOP
    @app_commands.command(
        name="stop",
        description="Stop playing music and disconnect the bot",
    )
    async def stop(self, ctx):
        # Get the voice client for the bot's current server
        voice_client = ctx.guild.voice_client

        # Check if the bot is playing music
        if not voice_client or not voice_client.is_playing():
            await ctx.send('The bot is not playing any music.')
            return

        # Stop playing the current song and disconnect the bot from the voice channel
        voice_client.stop()
        await voice_client.disconnect()


### BOT CONFIG AND START
# Load DISCORD_TOKEN from .env
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!',intents=intents)

@bot.event
async def on_start():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

async def main():
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())