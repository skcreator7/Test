from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader
from bson import ObjectId
import logging
import os

logger = logging.getLogger(__name__)

def create_app(db, bot):
    app = web.Application()
    setup_jinja2(app, loader=FileSystemLoader('templates'))
    app['db'] = db
    app['bot'] = bot
    app.router.add_get('/', home)
    app.router.add_get('/search', search)
    app.router.add_get('/watch', watch)
    app.router.add_static('/static/', path=os.path.abspath('static'))
    return app

@template('index.html')
async def home(request):
    return {"title": "Movie Bot Home"}

@template('search.html')
async def search(request):
    query = request.query.get('q', '')
    results = await request.app['db'].search_posts(query) if query else []
    return {
        "query": query,
        "results": results
    }

@template('watch.html')
async def watch(request):
    post_id = request.query.get('id')
    if not post_id:
        raise web.HTTPFound('/')
    try:
        post = await request.app['db'].posts.find_one({'_id': ObjectId(post_id)})
    except Exception:
        post = None
    return {
        "post": post,
        "links": post.get('links', []) if post else [],
        "link_count": len(post.get('links', [])) if post else 0
    }
