from aiohttp import web
from aiohttp_jinja2 import template
import logging

logger = logging.getLogger(__name__)

def setup_routes(app, db, bot):
    @app.get('/')
    @template('watch.html')
    async def index(request):
        return {'title': 'Telegram Posts Monitor'}

    @app.get('/search')
    @template('watch.html')
    async def search(request):
        query = request.query.get('q', '')
        results = []
        if query:
            results = await db.search_posts(query)
        return {'query': query, 'results': results}

    @app.post('/watch')
    async def watch_channel(request):
        data = await request.post()
        chat_id = data.get('chat_id')
        try:
            # Add chat to monitored list
            if chat_id not in Config.MONITORED_CHATS:
                Config.MONITORED_CHATS.append(int(chat_id))
                return web.json_response({'status': 'added'})
            return web.json_response({'status': 'exists'})
        except ValueError:
            return web.json_response({'error': 'Invalid chat ID'}, status=400)
