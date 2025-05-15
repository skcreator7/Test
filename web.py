from aiohttp import web
import aiohttp_jinja2
from bson import ObjectId

@aiohttp_jinja2.template('home.html')
async def handle_index(request):
    return {}

@aiohttp_jinja2.template('home.html')
async def handle_search(request):
    db = request.app['db']
    query = request.rel_url.query.get('q', '')
    if not query:
        return {'results': [], 'query': ''}

    cursor = db.posts.find({'$text': {'$search': query}})
    results = await cursor.to_list(length=50)
    return {'results': results, 'query': query}

@aiohttp_jinja2.template('watch.html')
async def handle_watch(request):
    db = request.app['db']
    post_id = request.match_info['post_id']

    post = await db.posts.find_one({'_id': ObjectId(post_id)})
    if not post:
        return web.Response(text="Post not found", status=404)

    links = post.get('links', [])
    return {'post': post, 'links': links, 'title': post.get('title', '')}

async def health_check(request):
    return web.Response(text="OK")
