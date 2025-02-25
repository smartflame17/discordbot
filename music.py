import asyncio
import discord
from discord.ext import commands
import yt_dlp as youtube_dl
from bot_token import allowed_channel_ids

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''
 
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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

#module wrapper with format options set
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.max_queue_size = 10

    # join user voice room if there is one with user in it
    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("Join a voice channel, dumbass")

    @commands.command()
    async def next(self, ctx):
        if len(self.queue) > 0:
            await self.skip(ctx)
    
    @commands.command()
    async def skip(self, ctx):
        if not ctx.voice_client:
            await ctx.send("Join a voice channel, idiot")
            return
            
        if not self.queue:  # check whether queue is empty
            await ctx.send("Add a music to the queue, butthead")
            return
        


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, original, *, data, volume = 0.5):
        super().__init__(original, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
    
    @classmethod
    async def from_url(cls, url, *, loop = None, stream = False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
 
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
 
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)