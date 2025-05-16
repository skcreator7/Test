from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
import jinja2
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_routes(app, db, bot):
    @app.get('/')
    @template('watch.html')
    async def index(request):
        return {'title': 'Telegram Posts Monitor'}

    @app.get('/watch')
    @template('watch.html')
    async def search(request):
        query = request.query.get('q', '')
        message_id = request.query.get('message_id', '')
        
        results = []
        if query:
            results = await db.search_posts(query, limit=20)
        
        return {
            'query': query,
            'results': results,
            'highlight_id': int(message_id) if message_id.isdigit() else None
        }

    @app.post('/watch')
    async def watch_channel(request):
        data = await request.post()
        chat_id = data.get('chat_id')
        try:
            if int(chat_id) not in Config.MONITORED_CHATS:
                Config.MONITORED_CHATS.append(int(chat_id))
                return web.json_response({'status': 'added'})
            return web.json_response({'status': 'exists'})
        except ValueError:
            return web.json_response({'error': 'Invalid chat ID'}, status=400)

def create_app(db, bot):
    app = web.Application()
    setup_jinja2(app, loader=jinja2.FileSystemLoader('templates'))
    setup_routes(app, db, bot)
    return app
