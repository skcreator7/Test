import asyncio
from aiohttp import web
from config import Config
from database import Database
from telegram_bot import TelegramBot

async def start_app():
    # Validate config
    Config.validate()
    print("✅ Config validated")

    # Initialize DB
    db = Database()
    await db.init_db()

    # Start bot
    bot = TelegramBot(db)
    asyncio.create_task(bot.start())

    # Web app
    app = web.Application()
    app['db'] = db

    async def on_shutdown(app):
        await bot.stop()
        await db.close()
        print("🛑 Clean shutdown complete")

    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    print("🚀 Starting application...")
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
