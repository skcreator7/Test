import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from database import Database
from web import create_app
from config import Config
import logging
import signal
from typing import Optional
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def on_shutdown(app: web.Application) -> None:
    """Graceful shutdown handler"""
    logger.info("Starting graceful shutdown...")
    shutdown_errors = False
    
    try:
        if 'bot' in app:
            logger.info("Stopping bot...")
            await app['bot'].stop()
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        shutdown_errors = True
        
    try:
        if 'db' in app:
            logger.info("Closing database...")
            await app['db'].close()
    except Exception as e:
        logger.error(f"Error closing database: {e}")
        shutdown_errors = True
        
    logger.info("Shutdown complete" + (" with errors" if shutdown_errors else ""))

async def start_app() -> web.Application:
    """Initialize all components"""
    try:
        logger.info("Initializing database...")
        db = Database(Config.MONGO_URI, Config.MONGO_DB)
        await db.initialize()
        
        logger.info("Starting Telegram bot...")
        bot = TelegramBot(db)
        await bot.initialize()
        
        logger.info("Creating web application...")
        app = create_app(db, bot)
        app.on_shutdown.append(on_shutdown)
        
        return app
    except Exception as e:
        logger.critical(f"Failed to initialize application: {e}")
        raise

def main():
    """Entry point with proper cleanup"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, loop.stop)
        
        # Start application
        app = loop.run_until_complete(start_app())
        
        # Configure web runner
        runner = web.AppRunner(app)
        loop.run_until_complete(runner.setup())
        
        site = web.TCPSite(runner, Config.HOST, Config.PORT)
        loop.run_until_complete(site.start())
        
        logger.info(f"Server running on http://{Config.HOST}:{Config.PORT}")
        loop.run_forever()
        
    except Exception as e:
        logger.critical(f"Application failed: {e}")
    finally:
        logger.info("Cleaning up...")
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logger.info("Application stopped")

if __name__ == "__main__":
    main()
