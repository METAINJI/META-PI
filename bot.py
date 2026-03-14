import os
import nextcord
from nextcord.ext import commands
from nextcord.ui import View, button
from nextcord import Interaction, SlashOption
import functools
import traceback
import datetime
import time
import asyncio
import psutil

TOKEN = os.getenv("DISCORD_TOKEN")

intents = nextcord.Intents.default()
bot = commands.Bot(intents=intents)

with open("pi.txt") as f:
    PI = f.read().replace("\n", "")

CONTEXT = 10


@bot.event
async def on_ready():
    print("Bot ready:", bot.user)

active_commands = {}

def prevent_overlap(func):
    
    @functools.wraps(func)
    async def wrapper(interaction: nextcord.Interaction, *args, **kwargs):
        user = interaction.user

        if active_commands.get(user.id, False):
            await interaction.response.send_message(
                "<a:Loading:1433393793704398929> 이전 명령어가 아직 처리 중입니다",
                ephemeral=True
            )
            return

        active_commands[user.id] = True
        try:
            return await func(interaction, *args, **kwargs)
        finally:
            active_commands.pop(user.id, None)

    return wrapper

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

    class ErrorView(View):
        def __init__(self):
            super().__init__(timeout=120)

        @button(label="세부사항 보기", style=nextcord.ButtonStyle.danger)
        async def details_button(self, button, i: nextcord.Interaction):
           
            await i.response.send_message(f"```py\n{full_traceback[:1900]}```", ephemeral=True)

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=ErrorView(), ephemeral=False)
        else:
            await interaction.response.send_message(embed=embed, view=ErrorView(), ephemeral=False)
    except Exception as e:
        print(f"⚠️ 오류 임베드 전송 실패: {e}")

bot_start_time = time.time()

def create_bar(value, max_value=100, length=20):
    filled_length = int(length * min(value, max_value) / max_value)
    empty_length = length - filled_length
    bar = "█" * filled_length + "░" * empty_length
    return bar

def format_uptime(seconds):
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, sec = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}일")
    if hours > 0:
        parts.append(f"{hours}시간")
    if minutes > 0:
        parts.append(f"{minutes}분")
    parts.append(f"{sec}초")
    return " ".join(parts)

@bot.slash_command(name="핑", description="봇의 상태를 확인합니다.")
@prevent_overlap
async def 핑(
    interaction: nextcord.Interaction,
    모드: str = nextcord.SlashOption(
        name="모드",
        description="표시할 정보 수준을 선택하세요",
        required=False,
        choices={"일반": "basic", "고급": "advanced"}
    )
):
    if 모드 is None:
        모드 = "basic"

    latency = round(bot.latency * 1000)
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    ram_used = mem.used / (1024**3)
    ram_total = mem.total / (1024**3)
    ram_percent = mem.percent
    uptime_sec = time.time() - bot_start_time
    uptime_str = format_uptime(uptime_sec)

    def status_check(v, limits):
        if v <= limits[0]:
            return "🟢 좋음"
        elif v <= limits[1]:
            return "🟡 보통"
        else:
            return "🔴 나쁨"

    cpu_status = status_check(cpu, (70, 90))
    ram_status = status_check(ram_percent, (70, 90))
    latency_status = status_check(latency, (150, 300))

    color_map = {"🟢 좋음": 0x00FFAA, "🟡 보통": 0xFFD700, "🔴 나쁨": 0xFF4C4C}
    max_status = max([cpu_status, ram_status, latency_status],
                     key=lambda s: ["🟢 좋음","🟡 보통","🔴 나쁨"].index(s))
    embed_color = color_map[max_status]

    cpu_bar = create_bar(cpu)
    ram_bar = create_bar(ram_percent)
    latency_bar = create_bar(min(latency, 500), max_value=500)

    embed = nextcord.Embed(
        title="🏓 퐁!",
        color=embed_color,
        timestamp=datetime.datetime.now(datetime.UTC)
    )

    embed.add_field(name=f"⏱️ 핑 {latency_status}", value=f"{latency}ms\n`{latency_bar}`", inline=False)
    embed.add_field(name=f"🖥️ CPU 사용량 {cpu_status}", value=f"{cpu}%\n`{cpu_bar}`", inline=False)
    embed.add_field(name=f"💾 RAM 사용량 {ram_status}", value=f"{ram_used:.2f}GB / {ram_total:.2f}GB ({ram_percent}%)\n`{ram_bar}`", inline=False)
    embed.add_field(name="⏳ 서버 가동 시간", value=uptime_str, inline=False)

    if 모드 == "advanced":
        embed.add_field(name="​", value="**─── 🛠️ 고급 정보 ───**", inline=False)

        guilds = len(bot.guilds)
        users = sum(g.member_count for g in bot.guilds)
        shards = bot.shard_count or 1

        net_before = psutil.net_io_counters()
        await asyncio.sleep(1)
        net_after = psutil.net_io_counters()
        upload_speed = (net_after.bytes_sent - net_before.bytes_sent) * 8 / (1024**2)  # Mbps
        download_speed = (net_after.bytes_recv - net_before.bytes_recv) * 8 / (1024**2)  # Mbps

        interfaces = psutil.net_if_stats()
        net_io_pernic = psutil.net_io_counters(pernic=True)
        iface_status_list = []
        max_speed_reference = 100
        for name, stats in interfaces.items():
            sent = net_io_pernic[name].bytes_sent / (1024**2)
            recv = net_io_pernic[name].bytes_recv / (1024**2)
            speed_mbps = stats.speed if stats.speed > 0 else max_speed_reference
            bar_length = int((speed_mbps / max_speed_reference) * 20)
            bar_length = min(bar_length, 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            status_emoji = "🟢" if stats.isup else "🔴"
            iface_status_list.append(
                f"{name} {status_emoji} `{bar}` ↑{sent:.1f}MB ↓{recv:.1f}MB ({speed_mbps}Mbps)"
            )
        iface_status_str = "\n".join(iface_status_list)

        embed.add_field(name="⬆️ 업로드 속도", value=f"{upload_speed:.2f} Mbps", inline=True)
        embed.add_field(name="⬇️ 다운로드 속도", value=f"{download_speed:.2f} Mbps", inline=True)
        embed.add_field(name="🌍 길드 수", value=str(guilds), inline=True)
        embed.add_field(name="👥 사용자 수", value=str(users), inline=True)
        embed.add_field(name="🧩 샤드", value=str(shards), inline=True)
        embed.add_field(name="💻 네트워크 인터페이스 상태", value=iface_status_str, inline=False)

    await interaction.response.send_message(embed=embed)

@bot.slash_command(description="파이에서 숫자 검색")
async def 파이검색(interaction: Interaction, number: str = SlashOption()):
    pos = PI.find(number)

    if pos == -1:
        await interaction.response.send_message("❌ 찾지 못했습니다")
        return

    start = max(0, pos - CONTEXT)
    end = pos + len(number) + CONTEXT

    context = PI[start:end]
    highlighted = context.replace(number, f"**{number}**")

    msg = f"""🔎 검색 결과

    위치: {pos}

    ...{highlighted}..."""

    await interaction.response.send_message(msg)


@bot.slash_command(description="파이 특정 자리 확인")
async def 파이자리(interaction: Interaction, position: int = SlashOption()):
    digit = PI[position]

    start = max(0, position - CONTEXT)
    end = position + CONTEXT + 1

    context = PI[start:end]

    highlighted = context.replace(digit, f"**{digit}**", 1)

    msg = f"""🔢 {position}번째 자리

    ...{highlighted}..."""

    await interaction.response.send_message(msg)


async def run_bot():

    await bot.start(TOKEN)
