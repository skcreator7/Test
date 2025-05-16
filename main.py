import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from database import Database
from web import create_app
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_app():
    # Initialize components
    db = Database(Config.MONGO_URI)
    await db.initialize()
    
    bot = TelegramBot(db)
    await bot.start()
    
    app = create_app(db, bot)
    return app

def main():
    try:
        web.run_app(
            start_app(),
            port=Config.PORT,
            handle_signals=True
        )
    except Exception as e:
        logger.error(f"Application failed: {e}")
        raise

if __name__ == "__main__":
    main()
