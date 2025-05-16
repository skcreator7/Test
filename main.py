import asyncio
import signal
import logging
from aiohttp import web
from web import create_app
from telegram_bot import TelegramBot
from database import Database
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def init_app():
    app = web.Application()
    
    # Initialize and store database
    db = Database(Config.MONGO_URI)
    await db.connect()
    app['db'] = db

    # Initialize and store bot
    bot = TelegramBot(db=db)
    await bot.start()
    app['bot'] = bot

    # Setup web routes
    await create_app(app)

    return app

async def shutdown(sig, loop, app):
    """Graceful shutdown handler"""
    logger.info(f"Received {sig.name}, shutting down...")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

    if 'bot' in app:
        await app['bot'].stop()
    if 'db' in app:
        await app['db'].close()

    loop.stop()

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        app = loop.run_until_complete(init_app())

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
