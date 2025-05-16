from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader
import logging
from config import Config

logger = logging.getLogger(__name__)

def setup_routes(app):
    """Setup all web routes"""
    router = app.router
    
    @router.get('/')
    @template('watch.html')
    async def index(request):
        return {'title': 'Telegram Posts Monitor'}

    @router.get('/watch')
    @template('watch.html')
    async def search(request):
        query = request.query.get('q', '')
        message_id = request.query.get('message_id', '')
        
        db = request.app['db']
        results = []
        if query:
            results = await db.search_posts(query, limit=20)
        
        return {
            'query': query,
            'results': results,
            'highlight_id': int(message_id) if message_id.isdigit() else None
        }

    @router.post('/watch')
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
    """Create and configure the web application"""
    app = web.Application()
    app['db'] = db
    app['bot'] = bot
    
    # Setup Jinja2 template engine
    setup_jinja2(app, loader=FileSystemLoader('templates'))
    
    # Setup routes
    setup_routes(app)
    
    return app
