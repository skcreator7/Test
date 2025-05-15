from aiohttp import web
from bson.objectid import ObjectId
import aiohttp_jinja2
from config import Config

# New: JSON API for mobile apps
async def api_search(request):
    db = request.app["db"]
    query = request.rel_url.query.get("q", "")
    limit = int(request.rel_url.query.get("limit", 10))
    results = await db.search_posts(query, limit=limit)
    return web.json_response({"results": results})

# New: Serve static files (CSS/JS)
async def setup_static_routes(app):
    app.router.add_static("/static/", path="static", name="static")

# Modified: Health check with DB ping
async def health_check(request):
    db = request.app["db"]
    try:
        await db.ping()
        return web.Response(text="OK")
    except Exception:
        return web.Response(status=500, text="DB Error")

# Your existing handlers...
def setup_routes(app):
    app.add_routes([
        web.get('/', handle_index),
        web.get('/api/search', api_search),  # New endpoint
        web.get('/health', health_check),
    ])
    setup_static_routes(app)  # New
