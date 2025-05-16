from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def setup_routes(app):
    # Static files
    app.router.add_static('/static/', path='static', name='static')
    
    # Web routes
    app.router.add_get('/', home)
    app.router.add_get('/watch', watch)
    app.router.add_get('/search', search)

@template('index.html')
async def home(request):
    return {"title": "Movie Bot"}

@template('watch.html')
async def watch(request):
    post_id = request.query.get('id')
    post = await request.app['db'].get_post(post_id) if post_id else None
    return {"post": post}

@template('search.html')
async def search(request):
    query = request.query.get('q')
    results = await request.app['db'].search_posts(query) if query else []
    return {
        "query": query,
        "results": results,
        "result_count": len(results)
    }

def create_app(db):
    app = web.Application()
    
    # Setup templates
    setup_jinja2(app, loader=FileSystemLoader('templates'))
    
    # Store database
    app['db'] = db
    
    # Setup routes
    setup_routes(app)
    
    return app
