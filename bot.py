import asyncio
import discord
from discord.ext import commands
from music import Music
from bot_token import token, allowed_channel_ids

import random

description = "빡쳐서 직접 만든 유튜브 음악봇"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

#init bot
bot = commands.Bot(command_prefix= '!', description=description, intents=intents)

#runs on startup
@bot.event
async def on_ready():
    print("Logging In...")
    print(f'Logged in to {bot.user}')
    print(f'ID: {bot.user.name}')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('도우-다'))

# list of allowed channel IDs that is used to verify allowed channels

def is_allowed_channel():
     def predicate(ctx):
          return ctx.channel.id in allowed_channel_ids
     return predicate

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
         await ctx.send("노래-봇 채널에서 커맨드 쓰셈 ㅇㅇ")

# hello
@bot.command()
@commands.check(is_allowed_channel())
async def sayhello(ctx):
    await ctx.send("hello")

# roll dice ind DnD style
@bot.command()
async def roll(ctx, dice:str):
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)

# exit voice channel
@bot.command()
@commands.check(is_allowed_channel())
async def out(ctx):
    await bot.voice_clients[0].disconnect()

async def main():
     async with bot:
          await bot.add_cog(Music(bot))
          await bot.start(token)
          print("Music class loaded and started")

asyncio.run(main())