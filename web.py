from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader
import logging

logger = logging.getLogger(__name__)

def create_app(db, bot):  # Now accepts both db and bot parameters
    """Application factory"""
    app = web.Application()
    
    # Setup templates
    setup_jinja2(app, loader=FileSystemLoader('templates'))
    
    # Store dependencies
    app['db'] = db
    app['bot'] = bot
    
    # Setup routes
    app.router.add_get('/', home)
    app.router.add_static('/static/', path='static')
    
    return app

@template('index.html')
async def home(request):
    return {"title": "Movie Bot"}
