import os
import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)
queues = {}


@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        voice_client = get(bot.voice_clients, guild=ctx.guild)

        if voice_client and voice_client.is_connected():
            await voice_client.move_to(channel)
        else:
            voice_client = await channel.connect()
            await ctx.send(f"Joined {channel.name}!")
    else:
        await ctx.send("You're not in a voice channel. Join a voice channel first.")


async def play_audio(ctx, url):
    voice_client = get(bot.voice_clients, guild=ctx.guild)
    if not voice_client or not voice_client.is_connected():
        await join(ctx)

    try:
        ydl_opts = {'format': 'bestaudio', 'noplaylist': 'True'}
        ffmpeg_opts = {
            'before_options':
                '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        voice_client.play(FFmpegPCMAudio(audio_url, **ffmpeg_opts))
        await ctx.send("Playing audio.")

    except Exception as e:
        await ctx.send(f"Error occurred while trying to play audio: {e}")


@bot.command()
async def play(ctx, url: str):
    if not url.startswith('https://www.youtube.com/watch?v='):
        await ctx.send("Please provide a valid YouTube video URL.")
        return

    if not ctx.author.voice:
        await ctx.send("You're not in a voice channel. Join a voice channel first.")
        return

    await play_audio(ctx, url)


@bot.command()
async def skip(ctx):
    voice_client = get(bot.voice_clients, guild=ctx.guild)

    if not voice_client or not voice_client.is_playing():
        await ctx.send("Nothing playing right now!")
        return

    voice_client.stop()
    await ctx.send('Skipping... Next song incoming!')
    if ctx.guild.id in queues and len(queues[ctx.guild.id]) > 0:
        next_url = queues[ctx.guild.id].pop(0)
        await play_audio(ctx, next_url)


@bot.command()
async def pause(ctx):
    voice_client = get(bot.voice_clients, guild=ctx.guild)

    if not voice_client or not voice_client.is_playing():
        await ctx.send("Nothing playing right now!")
        return

    voice_client.pause()
    await ctx.send('Paused.')


@bot.command()
async def resume(ctx):
    voice_client = get(bot.voice_clients, guild=ctx.guild)

    if not voice_client or not voice_client.is_paused():
        await ctx.send("Not paused.")
        return

    voice_client.resume()
    await ctx.send('Resumed.')


# Use environment variable for the Discord bot token
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if TOKEN is None:
    print("Discord bot token not found in environment variables.")
else:
    bot.run(TOKEN)
