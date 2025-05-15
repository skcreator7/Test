import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from config import Config
from database import Database

async def start_app():
    Config.validate()
    
    # Initialize DB with retry logic
    db = Database()
    await db.init_db()
    
    # Start bot
    bot = TelegramBot(db)
    asyncio.create_task(bot.start())  # Run in background
    
    # Setup web app
    app = web.Application()
    app["db"] = db
    
    # Clean shutdown
    async def on_shutdown(app):
        await bot.stop()
        await db.client.close()
    
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == "__main__":
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
