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

async def shutdown(signal, app):
    logger.info(f"Shutting down...")
    if 'bot' in app:
        await app['bot'].stop()
    if 'db' in app:
        await app['db'].close()
    await app.shutdown()
    await app.cleanup()

async def init_app():
    Config.validate()
    
    db = Database(Config.MONGO_URI, Config.MONGO_DB)
    await db.initialize()
    
    bot = TelegramBot(db)
    await bot.client.connect()
    
    app = create_app(db, bot)
    app.on_shutdown.append(lambda app: shutdown(signal.SIGTERM, app))
    
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
