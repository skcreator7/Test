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
    """Proper shutdown handling"""
    try:
        bot = app['bot']
        await bot.stop()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    finally:
        logger.info("Application shutdown complete")

async def start_app():
    """Initialize application with proper event loop"""
    db = Database(Config.MONGO_URI)
    await db.initialize()
    
    bot = TelegramBot(db)
    await bot.start()
    
    app = create_app(db, bot)
    app.on_shutdown.append(on_shutdown)
    return app

def main():
    """Main entry point with proper event loop handling"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Set up signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, loop.stop)
        
        app = loop.run_until_complete(start_app())
        
        # Run app with proper shutdown timeout
        web.run_app(
            app,
            host=Config.HOST,
            port=Config.PORT,
            handle_signals=True,
            shutdown_timeout=5.0
        )
    except Exception as e:
        logger.error(f"Application failed: {e}")
    finally:
        loop.close()
        logger.info("Application stopped")

if __name__ == "__main__":
    main()
