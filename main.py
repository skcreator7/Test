import asyncio
from aiohttp import web
from bot import TelegramBot
from database import Database
from web import (
    handle_index, handle_search,
    handle_watch, health_check
)
from config import Config

async def start_app():
    db = Database()
    await db.init_db()
    
    bot = TelegramBot(db)
    await bot.app.start()
    
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index),
        web.get('/search', handle_search),
        web.get('/watch/{post_id}', handle_watch),
        web.get('/health', health_check),
    ])
    
    app['db'] = db
    app['bot'] = bot
    
    return app

if __name__ == "__main__":
    print(f"Starting on {Config.HOST}:{Config.PORT}")
    print(f"Monitoring channel: {Config.SOURCE_CHANNEL_ID}")
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
