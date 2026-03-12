import nextcord
import os
from nextcord import SlashOption, Interaction, Embed, ButtonStyle, ui
from nextcord.ui import View, Select, button
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import functools
from ping3 import ping
import datetime
import traceback
from threading import Thread

from flask import (
    Flask,
    session,
    redirect,
    request,
    url_for,
    send_file,
    render_template_string
)

intents = nextcord.Intents.default()
bot = commands.Bot(intents=intents)


with open("pi.txt", "r") as f:
    PI = f.read().replace("\n", "").strip()

CONTEXT = 10  

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.sync_all_application_commands()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(e)

@bot.event
async def on_application_command_error(interaction: nextcord.Interaction, error: Exception):

    full_traceback = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    short_error = "".join(traceback.format_exception_only(type(error), error)).strip()

    embed = nextcord.Embed(
        title="❌ 오류 발생",
        description="명령어 사용 중 오류가 발생했습니다.",
        color=0xFF0000,
        timestamp=datetime.datetime.now(datetime.UTC)
    )
    embed.add_field(name="오류 코드", value=f"```{short_error}```", inline=False)
    embed.set_footer(text=f"요청자: {interaction.user}", icon_url=interaction.user.display_avatar.url)

    # 버튼 View 정의
    class ErrorView(View):
        def __init__(self):
            super().__init__(timeout=120)

        @button(label="세부사항 보기", style=nextcord.ButtonStyle.danger)
        async def details_button(self, button, i: nextcord.Interaction):
            # 버튼 누른 사람에게만 세부사항 출력
            await i.response.send_message(f"```py\n{full_traceback[:1900]}```", ephemeral=True)

    # 메시지 공개로 전송 (ephemeral=False)
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=ErrorView(), ephemeral=False)
        else:
            await interaction.response.send_message(embed=embed, view=ErrorView(), ephemeral=False)
    except Exception as e:
        print(f"⚠️ 오류 임베드 전송 실패: {e}")

active_commands = {}

def prevent_overlap(func):

    @functools.wraps(func)
    async def wrapper(interaction: nextcord.Interaction, *args, **kwargs):
        user = interaction.user

        if active_commands.get(user.id, False):
            await interaction.response.send_message(
                "이전 명령어가 아직 처리 중입니다",
                ephemeral=True
            )
            return

        active_commands[user.id] = True
        try:
            return await func(interaction, *args, **kwargs)
        finally:
            active_commands.pop(user.id, None)

    return wrapper


@bot.slash_command(description="파이에서 숫자를 검색합니다")
async def 파이검색(
    interaction: Interaction,
    number: str = SlashOption(description="검색할 숫자")
):

    if not number.isdigit():
        await interaction.response.send_message("❌ 숫자만 입력할 수 있습니다.", ephemeral=True)
        return

    pos = PI.find(number)

    if pos == -1:
        await interaction.response.send_message("❌ 파이에서 찾지 못했습니다.")
        return

    start = max(0, pos - CONTEXT)
    end = pos + len(number) + CONTEXT

    context = PI[start:end]
    highlighted = context.replace(number, f"**{number}**")

    arrow_pos = highlighted.find("**")
    arrow = " " * arrow_pos + "^"

    message = (
        f"🔎 검색 결과: {number}\n\n"
        f"📍 위치: {pos} 번째 자리\n\n"
        f"```text\n"
        f"...{highlighted}...\n"
        f"{arrow}\n"
        f"```"
    )

    await interaction.response.send_message(message)


@bot.slash_command(description="파이의 특정 자리 숫자를 확인합니다")
async def 파이자리(
    interaction: Interaction,
    position: int = SlashOption(description="확인할 자리")
):

    if position < 0 or position >= len(PI):
        await interaction.response.send_message("❌ 범위를 벗어난 자리입니다.")
        return

    start = max(0, position - CONTEXT)
    end = position + CONTEXT + 1

    context = PI[start:end]
    digit = PI[position]

    highlighted = context.replace(digit, f"**{digit}**", 1)

    arrow_pos = highlighted.find("**")
    arrow = " " * arrow_pos + "^"

    message = (
        f"🔢 파이의 {position} 번째 자리\n\n"
        f"```text\n"
        f"...{highlighted}...\n"
        f"{arrow}\n"
        f"```"
    )

    await interaction.response.send_message(message)

app = Flask('')

@app.route('/')
def home():
    return "✅ 봇이 온라인으로 전환되었습니다. 이제 이 창을 닫아도 됩니다."

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_web).start()

keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("ERROR: 환경 변수 DISCORD_TOKEN이 설정되어 있지 않습니다.")
    exit(1)

bot.run(TOKEN)


