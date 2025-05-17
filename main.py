import asyncio
from aiohttp import web
from web import create_app
from telegram_bot import TelegramBot
from database import Database
from config import Config
import logging
import signal

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def shutdown(signal, loop, app):
    logger.info(f"Received {signal.name}, initiating shutdown...")
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    if 'bot' in app:
        logger.info("Stopping Telegram bot...")
        await app['bot'].stop()
    
    if 'db' in app:
        logger.info("Closing database connection...")
        await app['db'].close()
    
    loop.stop()
    logger.info("Shutdown complete")

async def init_app():
    try:
        Config.validate()
        
        loop = asyncio.get_event_loop()
        
        db = Database(Config.MONGO_URI, Config.MONGO_DB)
        await db.initialize()
        
        bot = TelegramBot(db)
        await bot.initialize()
        
        app = create_app(db, bot)
        app['loop'] = loop
        
        return app
    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}")
        raise

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting application initialization...")
        app = loop.run_until_complete(init_app())
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(shutdown(s, loop, app))
        
        logger.info(f"Starting web server on {Config.HOST}:{Config.PORT}")
        web.run_app(
            app,
            host=Config.HOST,
            port=Config.PORT,
            access_log=logger,
            shutdown_timeout=5.0
        )
    except Exception as e:
        logger.critical(f"Application failed: {str(e)}")
    finally:
        loop.close()
        logger.info("Application fully stopped")

if __name__ == "__main__":
    main()
