import asyncio
import os
import uvicorn
from bot import run_bot
from web import app

async def start():
    loop = asyncio.get_event_loop()

    bot_task = loop.create_task(run_bot())

    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    server = uvicorn.Server(config)
    web_task = loop.create_task(server.serve())

    await asyncio.gather(bot_task, web_task)

asyncio.run(start())