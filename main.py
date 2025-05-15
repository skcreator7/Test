import asyncio
from aiohttp import web
from config import Config
from database import Database
from telegram_bot import TelegramBot

async def start_app():
    # Validate config
    try:
        Config.validate()
        print("✅ Config validation passed")
    except ValueError as e:
        print(f"❌ Config error: {e}")
        raise

    # Initialize DB
    db = Database()
    try:
        await db.init_db()
    except Exception as e:
        print(f"❌ DB init failed: {e}")
        raise

    # Start bot
    bot = TelegramBot(db)
    asyncio.create_task(bot.start())

    # Setup web app
    app = web.Application()
    app['db'] = db

    # Clean shutdown
    async def on_shutdown(app):
        await bot.stop()
        await db.close()
        print("🛑 Clean shutdown complete")

    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    print("🚀 Starting application...")
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
