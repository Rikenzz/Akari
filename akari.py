import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import youtube_dl
import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# DECLARING PREFIX AND INTENTS
bot = commands.Bot(command_prefix="!",intents = discord.Intents().all())

# AUDIO OPTIONS
ffmpeg_options = {
    'options': '-vn'
}

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
    'source_address': '0.0.0.0'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        #return filename
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


### ON_READY ###

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


### COMMANDS ###

@bot.tree.command(
    name = "play",
    description = "Akari plays music - autosearch or URL",
)
@app_commands.describe(song = "Music name or URL")
async def play(interaction: discord.Interaction, song: str):
    async with interaction.channel.typing():
        try:
            await interaction.user.voice.channel.connect()
            player = await YTDLSource.from_url(song, loop=bot.loop, stream=True)
            interaction.channel.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            
            await interaction.response.send_message(f"Now playing: {player.title}")
#discord.voice_client
        except:
            print(f"Can't play song")
            #await interaction.response.send_message("T'as cru que ça allait marcher ?", ephemeral=True)
    

@bot.tree.command(
    name = "vc",
    description = "Akari joins voice chat!"
)
async def vc(interaction: discord.Interaction):
    await interaction.user.voice.channel.connect()


async def ensure_voice(interaction: discord.Interaction):
    if interaction.client.voice_clients is None:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.response.send_message("You are not connected to a voice channel.")
            raise commands.CommandError("User not connected to a voice channel")



# BOT RUN
bot.run(DISCORD_TOKEN)