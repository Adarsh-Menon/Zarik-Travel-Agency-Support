"""
ZARIK — AI Travel Itinerary Assistant
Entry point: runs FastAPI server + Telegram bot polling
"""
import asyncio
import logging
import threading
import uvicorn
from fastapi import FastAPI

from api.routes import router
from bot.telegram_bot import create_bot_app
from config import FASTAPI_PORT, LOG_LEVEL

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("zarik")

# ── FastAPI App ─────────────────────────────────────────────

app = FastAPI(
    title="Zarik",
    description="AI Travel Itinerary Assistant — Lead Management API",
    version="0.1.0",
)
app.include_router(router)


# ── Run Both Services ───────────────────────────────────────

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=FASTAPI_PORT, log_level="info")


async def run_bot():
    bot_app = create_bot_app()
    logger.info("Starting Telegram bot (polling mode)...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()


def main():
    logger.info("🌍 Starting Zarik...")

    # Run FastAPI in a thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info(f"FastAPI running on port {FASTAPI_PORT}")

    # Run Telegram bot in main async loop
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
