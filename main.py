import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from config import Config
from database import Database
from web import health_check

async def start_app():
    # Validate config
    Config.validate()
    
    # Initialize DB
    db = Database()
    await db.init_db()
    
    # Start bot
    bot = TelegramBot(db)
    asyncio.create_task(bot.start())
    
    # Setup web app
    app = web.Application()
    app.add_routes([web.get('/health', health_check)])
    app['db'] = db
    
    # Clean shutdown
    async def on_shutdown(app):
        await bot.stop()
        await db.close()
    
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    print("🚀 Starting application...")
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
