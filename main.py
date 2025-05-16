import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from database import Database
from web import create_app
from config import Config
import logging
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def on_shutdown(app):
    """Handle application shutdown"""
    bot = app['bot']
    await bot.stop()

async def start_app():
    """Initialize and return application"""
    db = Database(Config.MONGO_URI)
    await db.initialize()
    
    bot = TelegramBot(db)
    await bot.start()
    
    app = create_app(db, bot)
    app['bot'] = bot
    app.on_shutdown.append(on_shutdown)
    return app

def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        app = loop.run_until_complete(start_app())
        
        web.run_app(
            app,
            port=Config.PORT,
            handle_signals=True
        )
    except Exception as e:
        logger.error(f"Application failed: {e}")
        raise

if __name__ == "__main__":
    main()
