import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from config import Config
from database import Database

async def start_app():
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        raise
    
    # Initialize database
    db = Database()
    try:
        await db.ping()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise
    
    # Start Telegram bot
    bot = TelegramBot(db)
    asyncio.create_task(bot.start())
    
    # Setup web application
    app = web.Application()
    app['db'] = db
    
    # Clean shutdown handler
    async def on_shutdown(app):
        await bot.stop()
        await db.client.close()
        print("🛑 Application shutdown complete")
    
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    print("🚀 Starting application...")
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
