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

async def shutdown(signal, loop, app):
    """Graceful shutdown handler"""
    logger.info(f"Received {signal.name}, shutting down...")
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    if 'bot' in app:
        await app['bot'].stop()
    
    if 'db' in app:
        await app['db'].close()
    
    loop.stop()

async def init_app():
    """Initialize application components"""
    Config.validate()
    
    # Initialize database
    db = Database(Config.MONGO_URI, Config.MONGO_DB)
    await db.initialize()
    
    # Initialize bot
    bot = TelegramBot(db)
    await bot.initialize()
    
    # Create web application
    app = create_app(db, bot)
    
    return app

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
            )
        
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
