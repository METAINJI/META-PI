import asyncio
import os
import uvicorn
import threading
import traceback
from bot import run_bot
from web import app


def run_web():
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 8080)),
            log_level="debug"
        )

    except Exception as e:
        print("[ERROR] Web server crashed:", e)
        traceback.print_exc()


async def main():
    print("STARTING")

    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

    try:
        await run_bot()
    except Exception as e:
        print("[ERROR] bot crashed:", e)
        traceback.print_exc()

    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
