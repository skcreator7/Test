import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2

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
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))

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
    web.run_app(start_app(), host=Config.HOST, port=Config.PORT)
