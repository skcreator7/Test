import asyncio
from aiohttp import web
from bot import TelegramBot
from database import Database
from web import (
    handle_index, handle_search, handle_watch, 
    handle_admin, handle_warnings, health_check
)
from config import Config

async def start_app():
    # Initialize Database
    db = Database()
    await db.init_db()
    
    # Initialize Telegram Bot
    bot = TelegramBot(db)
    await bot.app.start()
    
    # Setup Web Server
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index),
        web.get('/search', handle_search),
        web.get('/watch/{post_id}', handle_watch),
        web.get('/admin', handle_admin),
        web.get('/warnings', handle_warnings),
        web.get('/health', health_check),
    ])
    
    # Store instances in app context
    app['db'] = db
    app['bot'] = bot
    
    return app

if __name__ == "__main__":
    print(f"Starting server on {Config.HOST}:{Config.PORT}")
    print(f"Base URL: {Config.BASE_URL}")
    print(f"MongoDB: {Config.MONGO_URI}/{Config.MONGO_DB}")
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
