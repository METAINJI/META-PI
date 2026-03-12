import os
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption

TOKEN = os.getenv("DISCORD_TOKEN")

intents = nextcord.Intents.default()
bot = commands.Bot(intents=intents)

with open("pi.txt") as f:
    PI = f.read().replace("\n", "")

CONTEXT = 10


@bot.event
async def on_ready():
    print("Bot ready:", bot.user)


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

    arrow = " " * highlighted.find("**") + "^"

    msg = f"""🔎 검색 결과

위치: {pos}

```text
...{highlighted}...
{arrow}
```"""

    await interaction.response.send_message(msg)


@bot.slash_command(description="파이 특정 자리 확인")
async def 파이자리(interaction: Interaction, position: int = SlashOption()):
    digit = PI[position]

    start = max(0, position - CONTEXT)
    end = position + CONTEXT + 1

    context = PI[start:end]

    highlighted = context.replace(digit, f"**{digit}**", 1)

    arrow = " " * highlighted.find("**") + "^"

    msg = f"""🔢 {position}번째 자리

```text
...{highlighted}...
{arrow}
```"""

    await interaction.response.send_message(msg)


async def run_bot():
    await bot.start(TOKEN)