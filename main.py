import asyncio
from aiohttp import web
from web import create_app
from telegram_bot import TelegramBot
from database import Database
from config import Config
import logging
import signal

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def shutdown(signal, loop, app):
    """Graceful shutdown"""
    logger.info(f"Received {signal.name}, shutting down...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    if 'bot' in app:
        await app['bot'].stop()
    
    if 'db' in app:
        await app['db'].close()
    
    loop.stop()

async def init_app():
    """Initialize all components"""
    try:
        logger.info("Validating configuration...")
        Config.validate()
        
        logger.info("Initializing database...")
        db = Database(Config.MONGO_URI, Config.MONGO_DB)
        await db.initialize()
        
        logger.info("Starting Telegram bot...")
        bot = TelegramBot(db)
        await bot.initialize()
        
        logger.info("Creating web application...")
        app = create_app(db, bot)
        
        return app
    except Exception as e:
        logger.critical(f"Initialization failed: {e}")
        raise

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        app = loop.run_until_complete(init_app())
        
        # Signal handling
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig, 
                lambda s=sig: asyncio.create_task(shutdown(s, loop, app))
        
        # Start web server
        web.run_app(
            app,
            host=Config.HOST,
            port=Config.PORT,
            access_log=logger,
            shutdown_timeout=5.0
        )
    except Exception as e:
        logger.critical(f"Application failed: {e}")
    finally:
        loop.close()
        logger.info("Application stopped")

if __name__ == "__main__":
    logger.info("Starting application...")
    main()
