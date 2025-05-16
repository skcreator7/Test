import asyncio
import logging
from pyrogram import Client
from motor.motor_asyncio import AsyncIOMotorClient
from web import create_app
from bot import TelegramBot
from aiohttp import web
import os

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
BASE_URL = os.getenv("BASE_URL", "https://your-koyeb-url.koyeb.app")

# MongoDB
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["telegram_stream_bot"]

# Pyrogram Bot Client
bot_client = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


async def main():
    await bot_client.start()

    # Create bot logic
    telegram_bot = TelegramBot(bot_client, db)

    # Start web server
    app = create_app(db, telegram_bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    logger.info("Bot and web server running at http://0.0.0.0:8000")

    await asyncio.Event().wait()  # Keep running


if __name__ == "__main__":
    asyncio.run(main())
