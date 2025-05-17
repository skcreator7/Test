import asyncio
from aiohttp import web
from web import create_app
from telegram_bot import TelegramBot
from database import Database
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def on_startup(app):
    await app['bot'].start()

async def on_shutdown(app):
    logger.info("Shutting down...")
    if 'bot' in app:
        await app['bot'].stop()
    if 'db' in app:
        await app['db'].close()

async def init_app():
    Config.validate()
    db = Database(Config.MONGO_URI, Config.MONGO_DB)
    await db.initialize()
    bot = TelegramBot(db)
    app = create_app(db, bot)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        app = loop.run_until_complete(init_app())
        web.run_app(
            app,
            host=Config.HOST,
            port=Config.PORT,
            access_log=None
        )
    except Exception as e:
        logger.critical(f"Failed to start: {e}")
    finally:
        loop.close()

if __name__ == "__main__":
    main()
