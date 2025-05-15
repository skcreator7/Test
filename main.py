import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2

from database import Database
from telegram_bot import TelegramBot
from config import Config
from web import handle_index, handle_search, handle_watch, health_check

async def start_app():
    # Validate configuration
    Config.validate()
    
    # Initialize Database
    db = Database()
    await db.init_db()
    
    # Start Telegram Bot
    bot = TelegramBot(db)
    await bot.start()
    
    # Setup Web Application
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))
    
    # Add Routes
    app.add_routes([
        web.get('/', handle_index),
        web.get('/search', handle_search),
        web.get('/watch/{post_id}/{title}', handle_watch),
        web.get('/health', health_check),
    ])
    
    app['db'] = db
    return app

if __name__ == "__main__":
    print(f"Starting server on {Config.HOST}:{Config.PORT}")
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
