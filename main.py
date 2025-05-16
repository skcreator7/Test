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
    logger.info("Application shutdown complete")

async def start_app():
    """Initialize and return application"""
    # Initialize database
    db = Database(Config.MONGO_URI)
    await db.initialize()
    
    # Initialize bot
    bot = TelegramBot(db)
    await bot.start()
    
    # Create web application
    app = create_app(db, bot)
    app.on_shutdown.append(on_shutdown)
    
    return app

def main():
    try:
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start application
        app = loop.run_until_complete(start_app())
        
        # Run web server
        web.run_app(
            app,
            port=Config.PORT,
            handle_signals=True,
            shutdown_timeout=60.0
        )
    except Exception as e:
        logger.error(f"Application failed: {e}")
        raise
    finally:
        logger.info("Application stopped")

if __name__ == "__main__":
    main()
