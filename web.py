import aiohttp_jinja2
from aiohttp import web
from bson.objectid import ObjectId
from config import Config

@aiohttp_jinja2.template('index.html')
async def handle_index(request):
    return {}

@aiohttp_jinja2.template('search.html')
async def handle_search(request):
    query = request.rel_url.query.get("q", "").strip()
    db = request.app["db"]
    posts = await db.search_posts(query)
    return {"query": query, "results": posts, "BASE_URL": Config.BASE_URL}

@aiohttp_jinja2.template('watch.html')
async def handle_watch(request):
    db = request.app["db"]
    post_id = request.match_info['post_id']
    title = request.match_info['title']
    post = await db.get_post(ObjectId(post_id))

    if not post:
        raise web.HTTPNotFound(text="Post not found")

    links = post.get("links", [])
    if len(links) <= 3:
        buttons = [{"label": q, "url": u} for q, u in links]
    else:
        buttons = [{"label": f"Episode {i+1}", "url": u} for i, (_, u) in enumerate(links)]

    return {
        "title": post.get("title", title),
        "buttons": buttons,
        "BASE_URL": Config.BASE_URL
    }

async def health_check(request):
    return web.Response(text="OK")
