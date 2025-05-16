import asyncio
from aiohttp import web
from web import create_app
from telegram_bot import TelegramBot
from database import Database
from config import Config
import logging
import signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def on_shutdown(app: web.Application):
    """Handle graceful shutdown"""
    logger.info("Starting shutdown...")
    try:
        if 'bot' in app:
            await app['bot'].stop()
        if 'db' in app:
            await app['db'].close()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    logger.info("Shutdown complete")

async def init_app():
    """Initialize application components"""
    # Validate config first
    Config.validate()
    
    # Initialize database
    db = Database(Config.MONGO_URI, Config.MONGO_DB)
    await db.initialize()
    
    # Initialize bot
    bot = TelegramBot(db)
    await bot.initialize()
    
    # Create web application
    app = create_app(db, bot)
    app.on_shutdown.append(on_shutdown)
    
    return app

def main():
    """Entry point"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, loop.stop)
        
        # Initialize and run app
        app = loop.run_until_complete(init_app())
        web.run_app(
            app,
            host=Config.HOST,
            port=Config.PORT,
            shutdown_timeout=5.0
        )
    except Exception as e:
        logger.critical(f"Application failed: {e}")
    finally:
        loop.close()
        logger.info("Application stopped")

if __name__ == "__main__":
    main()
