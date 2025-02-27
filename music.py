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
    #'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = [] # holds tuples of ({music_url}, {music_title})
        self.current_song = None  # Currently playing song
        self.max_queue_size = 10
        self.volume = 0.5    # default volume

    # join user voice room if there is one with user in it
    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("Join a voice channel, dumbass")

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, url):
        try:
        # auto-join
            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()
        
            if len(self.queue) >= self.max_queue_size:
                await ctx.send("Max Queue size reached: Remove from queue or edit queue size with !set_queue_size")
                return
        
            # fetch song info first and display queue info
            async with ctx.typing():
                song = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

                if not ctx.voice_client.is_playing():   #if not playing any song, play immediately
                    self.current_song = song
                    ctx.voice_client.play(song, after=lambda _: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))   #run play_next after song ends
                    await ctx.send(f"Now Playing: {self.current_song.title}")
                else:   # else append to queue
                    self.queue.append((url, song.title))
                    queue_info = f"Added {song.title} to Queue\nCurrently {len(self.queue)} songs on queue:\n"
                    for i, (_, title) in enumerate(self.queue, 1):
                        queue_info += f"{i}. {title}\n"
                    await ctx.send(queue_info)
                    print(queue_info)

        except Exception as e:
            await ctx.send(f"Error while adding music to queue : {str(e)}")
            print(f"Play Error : {e}")

    # inner logic for playing music / managing music inside queue
    # IS NOT A COMMAND!!
    async def play_next(self, ctx):
        if not ctx.voice_client:
            return
        
        try:
            if len(self.queue) > 0:
                # if song ends, play next song in queue (if there is any)
                next_url, next_title = self.queue.pop(0)
                self.current_song = await YTDLSource.from_url(next_url, loop=self.bot.loop, stream=True)
                ctx.voice_client.play(self.current_song, after=lambda _: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
                await ctx.send(f"Now Playing: {self.current_song.title}")
                print(f"Now Playing: {self.current_song.title}")
        except Exception as e:
            await ctx.send(f"Error while adding music to queue : {str(e)}")
            print(f"Play Error : {e}")

    @commands.command(aliases=["n"])
    async def next(self, ctx):
        if len(self.queue) > 0:
            await self.skip(ctx)
    
    @commands.command(aliases=["s"])
    async def skip(self, ctx):
        if not ctx.voice_client:
            await ctx.send("Join a voice channel, idiot")
            return
            
        if not self.queue:  # check whether queue is empty
            await ctx.send("Queue empty. Add a music to the queue, butthead")
            return
        # pause current playing song
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        try:
            current_url, current_title = self.queue.pop(0)  #pop from queue to get next song

            self.current_song = await YTDLSource.from_url(current_url, loop= self.bot.loop, stream=True)
            ctx.voice_client.play(self.current_song, after=lambda _: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            await ctx.send(f"Now Playing : {self.current_song.title}")
            print(f"Now Playing: {self.current_song.title}")
        
        except Exception as e:
            await ctx.send("Error while playing song")
            if current_url and current_title:
                self.queue.insert(0, (current_url, current_title))

    @commands.command(aliases=["v"])
    async def volume(self, ctx, volume:int):
        if not ctx.voice_client:
            await ctx.send("Join a voice channel, idiot")
            return
        
        if not 0 <= volume <= 100:
            await ctx.send("Volume must be between 0% ~ 100%")

        ctx.voice_client.source.volume = volume/100
        await ctx.send(f"Volume set to {volume}%")
        
    @commands.command()
    async def stop(self, ctx):
        # stops song, clears queue and leaves
        if not ctx.voice_client:
            await ctx.send("Bot is idle")
            return
        self.queue.clear()
        self.current_song = None

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("Farewell bitches")
    
    @commands.command()
    async def pause(self, ctx):
        if not ctx.voice_client:
            await ctx.send("Bot is idle")
            return
        if ctx.voice_client.is_paused() or not ctx.voice_client.is_playing():
            await ctx.send("Song is already paused or not playing")
            return
        ctx.voice_client.pause()
        await ctx.send(f"Paused current song: {self.current_song.title}")
        print(f"Paused current song: {self.current_song.title}")
    
    @commands.command()
    async def resume(self, ctx):
        if not ctx.voice_client:
            await ctx.send("Bot is idle")
            return
        if ctx.voice_client.is_playing() or not ctx.voice_client.is_paused():
            await ctx.send("Song is already playing or there is no song to play")
            return
        ctx.voice_client.resume()
        await ctx.send(f"Resuming current song: {self.current_song.title}")
        print(f"Resuming current song: {self.current_song.title}")

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if len(self.queue) == 0:
            await ctx.send("Queue is empty")
            return
        queue_info = f"Currently {len(self.queue)} songs on queue:\n"
        for i, (_, title) in enumerate(self.queue, 1):
            queue_info += f"{i}. {title}\n"
        await ctx.send(queue_info)
        # prints out queue info

#wrapper class for discord's FFmpegPCMAudio that saves title, url and data as well
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
        #print(f"File Obtained : {filename}")
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)