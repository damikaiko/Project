# -*- coding: utf-8 -*-
import discord
from discord.ext import tasks
from discord import app_commands
import asyncio
from dotenv import load_dotenv
import os

# .env ファイルを読み込む
load_dotenv()

# .env から TOKEN を取得
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
VC_CHANNEL_ID = int(os.getenv("VC_CHANNEL_ID"))

WORK_DURATION = 60 * 60  # 作業 60分
BREAK_DURATION = 15 * 60  # 休憩 15分

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

voice_client: discord.VoiceClient = None
timer_running = False

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("スラッシュコマンドが同期されました")

async def connect_to_vc():
    global voice_client
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    vc_channel = discord.utils.get(guild.voice_channels, id=VC_CHANNEL_ID)
    if vc_channel:
        voice_client = await vc_channel.connect()

async def play_mp3(filename):
    if voice_client and voice_client.is_connected():
        source = discord.FFmpegPCMAudio(filename)
        voice_client.play(source)
        while voice_client.is_playing():
            await asyncio.sleep(1)

@tasks.loop(seconds=0)
async def pomodoro_loop():
    global timer_running
    while timer_running:
        print("作業スタート！")
        await play_mp3("work.mp3")
        await asyncio.sleep(WORK_DURATION)

        print("休憩スタート！")
        await play_mp3("break.mp3")
        await asyncio.sleep(BREAK_DURATION)

@tree.command(name="timer", description="ポモロードタイマーを開始します", guild=discord.Object(id=GUILD_ID))
async def start_timer(interaction: discord.Interaction):
    global timer_running
    if timer_running:
        await interaction.response.send_message("すでにタイマーが動いています！", ephemeral=True)
        return

    await interaction.response.send_message("ポモロードタイマーを開始します！")
    await connect_to_vc()
    timer_running = True
    pomodoro_loop.start()

@tree.command(name="stop", description="ポモロードタイマーを停止します", guild=discord.Object(id=GUILD_ID))
async def stop_timer(interaction: discord.Interaction):
    global timer_running, voice_client
    if not timer_running:
        await interaction.response.send_message("タイマーは動いていません。", ephemeral=True)
        return

    timer_running = False
    pomodoro_loop.stop()
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        voice_client = None

    await interaction.response.send_message("タイマーを停止し、VCから切断しました。")

bot.run(TOKEN)