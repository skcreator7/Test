from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader
import logging
from config import Config

logger = logging.getLogger(__name__)

def setup_routes(app):
    """Setup all web routes"""
    
    @template('watch.html')
    async def index(request):
        return {'title': 'Telegram Posts Monitor'}
    
    @template('watch.html')
    async def search(request):
        db = request.app['db']
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
    
    async def watch_channel(request):
        db = request.app['db']
        data = await request.post()
        chat_id = data.get('chat_id')
        try:
            if int(chat_id) not in Config.MONITORED_CHATS:
                Config.MONITORED_CHATS.append(int(chat_id))
                return web.json_response({'status': 'added'})
            return web.json_response({'status': 'exists'})
        except ValueError:
            return web.json_response({'error': 'Invalid chat ID'}, status=400)

    # Add routes directly to the app router
    app.router.add_get('/', index)
    app.router.add_get('/watch', search)
    app.router.add_post('/watch', watch_channel)

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
