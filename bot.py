import os
from dotenv import load_dotenv
import nextcord
import random
from nextcord.ext import commands
from nextcord.ui import View, button, Modal, TextInput
from nextcord import Interaction, SlashOption
import functools
import traceback
import datetime
import time
import math
import asyncio
import psutil

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN").strip()

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
    value = max(0, min(value, max_value)) 
    filled_length = int(length * value / max_value)
    empty_length = length - filled_length
    return "█" * filled_length + "░" * empty_length

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

    await interaction.response.defer()

    if 모드 is None:
        모드 = "basic"

    cpu = psutil.cpu_percent(interval=0.5)

    latency = round(bot.latency * 1000)
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

    status_order = {"🟢 좋음": 0, "🟡 보통": 1, "🔴 나쁨": 2}

    cpu_status = status_check(cpu, (70, 90))
    ram_status = status_check(ram_percent, (70, 90))
    latency_status = status_check(latency, (150, 300))

    color_map = {"🟢 좋음": 0x00FFAA, "🟡 보통": 0xFFD700, "🔴 나쁨": 0xFF4C4C}

    max_status = max(
        [cpu_status, ram_status, latency_status],
        key=lambda s: status_order[s]
    )

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
    embed.add_field(name=f"💾 RAM 사용량 {ram_status}",
                    value=f"{ram_used:.2f}GB / {ram_total:.2f}GB ({ram_percent}%)\n`{ram_bar}`",
                    inline=False)
    embed.add_field(name="⏳ 서버 가동 시간", value=uptime_str, inline=False)

    if 모드 == "advanced":
        embed.add_field(name="", value="**─── 🛠️ 고급 정보 ───**", inline=False)

        guilds = len(bot.guilds)
        users = sum(g.member_count or 0 for g in bot.guilds)
        shards = bot.shard_count or 1

        net1 = psutil.net_io_counters()
        await asyncio.sleep(0.2) 
        net2 = psutil.net_io_counters()

        upload_speed = (net2.bytes_sent - net1.bytes_sent) * 8 / (1024**2) / 0.2
        download_speed = (net2.bytes_recv - net1.bytes_recv) * 8 / (1024**2) / 0.2

        interfaces = psutil.net_if_stats()
        net_io_pernic = psutil.net_io_counters(pernic=True)

        iface_status_list = []

        for name, stats in interfaces.items():
            if name not in net_io_pernic:
                continue

            sent = net_io_pernic[name].bytes_sent / (1024**2)
            recv = net_io_pernic[name].bytes_recv / (1024**2)

            speed = stats.speed if stats.speed > 0 else 100

            bar = create_bar(speed, max_value=100)
            status_emoji = "🟢" if stats.isup else "🔴"

            iface_status_list.append(
                f"{name} {status_emoji} `{bar}` ↑{sent:.1f}MB ↓{recv:.1f}MB ({speed}Mbps)"
            )

        iface_status_str = "\n".join(iface_status_list)

        if len(iface_status_str) > 1000:
            iface_status_str = iface_status_str[:1000] + "\n..."

        embed.add_field(name="⬆️ 업로드 속도", value=f"{upload_speed:.2f} Mbps", inline=True)
        embed.add_field(name="⬇️ 다운로드 속도", value=f"{download_speed:.2f} Mbps", inline=True)
        embed.add_field(name="🌍 길드 수", value=str(guilds), inline=True)
        embed.add_field(name="👥 사용자 수", value=str(users), inline=True)
        embed.add_field(name="🧩 샤드", value=str(shards), inline=True)
        embed.add_field(name="💻 네트워크 인터페이스 상태", value=iface_status_str, inline=False)

    await interaction.followup.send(embed=embed)


class JumpModal(Modal):
    def __init__(self, view: "PiSearchView"):
        super().__init__(title="번호로 이동")
        self.view = view

        self.input = TextInput(
            label="이동할 번호 (1 ~ {})".format(len(view.positions)),
            placeholder="예: 314",
            required=True
        )
        self.add_item(self.input)

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.view.user_id:
            await interaction.response.send_message("❌ 본인만 사용 가능", ephemeral=True)
            return

        try:
            value = int(self.input.value)
        except:
            await interaction.response.send_message("❌ 숫자만 입력", ephemeral=True)
            return

        if not (1 <= value <= len(self.view.positions)):
            await interaction.response.send_message("❌ 이동 가능 범위 초과", ephemeral=True)
            return

        self.view.index = value - 1

        await interaction.response.edit_message(
            content=self.view.get_message(),
            view=self.view
        )

MAX_RESULTS = 10000
CONTEXT = 10

def search_pi(q: str):
    positions = []
    start = 0
    count = 0

    while True:
        pos = PI.find(q, start)
        if pos == -1:
            break

        count += 1

        if len(positions) < MAX_RESULTS:
            positions.append(pos)

        if count >= MAX_RESULTS:
            break

        start = pos + len(q) 

    return positions, count


class PiSearchView(View):
    def __init__(self, positions, number, user_id, total_count):
        super().__init__(timeout=120)
        self.positions = positions
        self.number = number
        self.user_id = user_id
        self.index = 0
        self.total_count = total_count
        self.message = None 

    def get_message(self):
        pos = self.positions[self.index]

        start = max(0, pos - CONTEXT)
        end = pos + len(self.number) + CONTEXT

        ctx = PI[start:end]

        if start == 0:
            ctx = "3." + ctx[1:]

        i = ctx.find(self.number)

        if i != -1:
            highlight = (
                ctx[:i] +
                f"**{self.number}**" +
                ctx[i + len(self.number):]
            )
        else:
            highlight = ctx
    
        prefix = "" if start == 0 else "..."
        suffix = "..."

        total_text = (
            f"{self.total_count:,}"
            if self.total_count < MAX_RESULTS
            else f"{MAX_RESULTS:,}+"
        )

        return f"""🔎 검색 결과

위치: {pos:,}
({self.index+1} / {len(self.positions)})

총 개수: {total_text}

{prefix}{highlight}{suffix}
"""

    @button(label="⬅ 이전", style=nextcord.ButtonStyle.secondary)
    async def prev_btn(self, button, interaction: Interaction):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 본인만 사용 가능", ephemeral=True)
            return

        if self.index > 0:
            self.index -= 1

        await interaction.response.edit_message(
            content=self.get_message(),
            view=self
        )

    @button(label="다음 ➡", style=nextcord.ButtonStyle.primary)
    async def next_btn(self, button, interaction: Interaction):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ 본인만 사용 가능", ephemeral=True)
            return

        if self.index < len(self.positions) - 1:
            self.index += 1

        await interaction.response.edit_message(
            content=self.get_message(),
            view=self
        )

    @button(label="↹ 이동", style=nextcord.ButtonStyle.success)
    async def jump_btn(self, button, interaction: Interaction):
        
        await interaction.response.send_modal(JumpModal(self))
 
        async def on_timeout(self):
            for child in self.children:
                child.disabled = True

            if self.message:
                await self.message.edit(view=self) 


@bot.slash_command(description="파이에서 숫자 검색")
async def 파이검색(interaction: Interaction, number: str = SlashOption()):

    await interaction.response.defer()
    
    positions, count = search_pi(number)

    if not positions:
        await interaction.followup.send("❌ 찾지 못했습니다")
        return
    
    view = PiSearchView(positions, number, interaction.user.id, count)

    msg = await interaction.followup.send(
        content=view.get_message(),
        view=view
    )

    view.message = msg

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

def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

@bot.slash_command(name="소수판별", description="숫자가 소수인지 판별합니다.")
async def prime_check(
    interaction: nextcord.Interaction,
    number: int = nextcord.SlashOption(description="판별할 숫자 입력")
):
    result = is_prime(number)

    if result:
        await interaction.response.send_message(f"✅ {number}은(는) 소수입니다.")
    else:
        await interaction.response.send_message(f"❌ {number}은(는) 소수가 아닙니다.")


def prime_factorization(n: int):
    factors = []
    
    while n % 2 == 0:
        factors.append(2)
        n //= 2

    for i in range(3, int(math.sqrt(n)) + 1, 2):
        while n % i == 0:
            factors.append(i)
            n //= i

    if n > 2:
        factors.append(n)

    return factors

@bot.slash_command(name="소인수분해", description="숫자를 소인수분해합니다.")
async def factor(
    interaction: nextcord.Interaction,
    number: int = nextcord.SlashOption(description="숫자 입력")
):
    if number <= 1:
        await interaction.response.send_message("❌ 2 이상의 정수를 입력해주세요.")
        return

    factors = prime_factorization(number)
    result = " × ".join(map(str, factors))

    await interaction.response.send_message(f"🔢 {number} = {result}")

@bot.slash_command(name="최대공약수", description="최대공약수를 구합니다.")
async def gcd_command(
    interaction: nextcord.Interaction,
    a: int,
    b: int
):
    result = math.gcd(a, b)
    await interaction.response.send_message(f"📊 ({a}, {b})의 최대공약수 = {result}")

@bot.slash_command(name="최소공배수", description="최소공배수를 구합니다.")
async def lcm_command(
    interaction: nextcord.Interaction,
    a: int,
    b: int
):
    result = abs(a * b) // math.gcd(a, b)
    await interaction.response.send_message(f"📊 ({a}, {b})의 최소공배수 = {result}")

@bot.slash_command(name="랜덤", description="범위 내 랜덤 숫자 생성")
async def random_number(
    interaction: nextcord.Interaction,
    min: int,
    max: int
):
    if min > max:
        await interaction.response.send_message("❌ min이 max보다 클 수 없습니다.")
        return

    value = random.randint(min, max)
    await interaction.response.send_message(f"🎲 결과: {value}")

@bot.slash_command(name="주사위", description="주사위를 굴립니다.")
async def dice(
    interaction: nextcord.Interaction,
    sides: int = nextcord.SlashOption(description="면 개수", default=6)
):
    if sides < 2:
        await interaction.response.send_message("❌ 최소 2면 이상이어야 합니다.")
        return

    value = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 {sides}면 주사위 결과: {value}")

async def run_bot():

    await bot.start(TOKEN)
