import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from database import Database
from web import setup_routes
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_bot(db):
    bot = TelegramBot(db)
    if not await bot.start():
        raise RuntimeError("Failed to start Telegram bot")
    return bot

async def start_app():
    # Initialize components
    db = Database(Config.MONGO_URI)
    await db.initialize()
    
    bot = await start_bot(db)
    
    # Create web application
    app = web.Application()
    setup_routes(app, db, bot)
    
    # Add health check endpoint
    async def health_check(request):
        return web.Response(text="OK")
    
    app.router.add_get('/health', health_check)
    
    return app

def main():
    try:
        web.run_app(
            start_app(),
            port=Config.PORT,
            handle_signals=True,
            shutdown_timeout=5.0
        )
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
