import asyncio
from aiohttp import web
from config import Config
from database import Database
from telegram_bot import TelegramBot
from web import health_check

async def start_bot(db):
    """Initialize and start bot with connection handling"""
    bot = TelegramBot(db)
    await bot.start()
    return bot

async def start_app():
    # Validate config first
    Config.validate()
    print("✅ Config validated")

    # Initialize DB
    db = Database()
    await db.init_db()
    print("✅ Database initialized")

    # Start bot
    bot = await start_bot(db)
    print("✅ Bot started")

    # Setup web app
    app = web.Application()
    app.add_routes([web.get('/health', health_check)])
    app['db'] = db
    app['bot'] = bot

    async def on_shutdown(app):
        print("🛑 Starting shutdown sequence...")
        try:
            await bot.stop()
            print("✅ Bot stopped")
        except Exception as e:
            print(f"⚠️ Error stopping bot: {e}")
        
        try:
            await db.close()
            print("✅ Database connection closed")
        except Exception as e:
            print(f"⚠️ Error closing database: {e}")
        
        print("🛑 Shutdown complete")

    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    print("🚀 Starting application...")
    web.run_app(
        start_app(),
        host=Config.HOST,
        port=Config.PORT,
        handle_signals=True  # Proper signal handling
    )
