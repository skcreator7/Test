import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from config import Config
from database import Database
from web import health_check

async def start_bot(db):
    """Initialize and start bot separately"""
    bot = TelegramBot(db)
    await bot.start()
    return bot

async def start_app():
    # Validate config
    Config.validate()
    
    # Initialize DB
    db = Database()
    await db.init_db()
    
    # Start bot in background
    bot_task = asyncio.create_task(start_bot(db))
    
    # Setup web app
    app = web.Application()
    app.add_routes([web.get('/health', health_check)])
    app['db'] = db
    
    # Clean shutdown
    async def on_shutdown(app):
        bot = await bot_task
        await bot.stop()
        await db.close()
        print("🛑 Clean shutdown complete")
    
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    print("🚀 Starting application...")
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
