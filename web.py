from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader
import logging

logger = logging.getLogger(__name__)

def setup_routes(app):
    """Safe route setup without decorators"""
    async def index(request):
        return {'title': 'Movie Search'}
    
    async def watch(request):
        bot = request.app['bot']
        post_id = request.query.get('post_id')
        chat_id = request.query.get('chat_id')
        
        post = None
        if post_id and chat_id:
            try:
                posts = await bot.db.search_posts("", limit=50)
                post = next((p for p in posts 
                           if str(p['message_id']) == post_id 
                           and str(p['chat_id']) == chat_id), None)
            except Exception as e:
                logger.error(f"Post lookup error: {e}")
        
        return {
            'post': post,
            'query': request.query.get('q', '')
        }
    
    app.router.add_get('/', index)
    app.router.add_get('/watch', watch)

def create_app(db, bot):
    """Create application with proper setup"""
    app = web.Application()
    app['db'] = db
    app['bot'] = bot
    
    # Setup Jinja2
    setup_jinja2(
        app, 
        loader=FileSystemLoader('templates'),
        auto_reload=False
    )
    
    setup_routes(app)
    return app
