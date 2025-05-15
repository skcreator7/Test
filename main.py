import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from config import Config
from database import Database
from web import setup_routes

async def start_app():
    Config.validate()
    
    # Initialize DB with retries for Koyeb
    db = Database()
    await db.init_db(max_retries=3, retry_delay=5)
    
    # Start bot
    bot = TelegramBot(db)
    asyncio.create_task(bot.start())  # Run in background
    
    # Setup web app
    app = web.Application()
    app["db"] = db
    setup_routes(app)
    
    # Koyeb needs clean shutdown
    async def on_shutdown(app):
        await bot.stop()
        await db.close()
    
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
