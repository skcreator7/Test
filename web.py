from aiohttp import web
import aiohttp_jinja2
from bson import ObjectId

@aiohttp_jinja2.template('home.html')
async def handle_index(request):
    return {'results': [], 'query': ''}

@aiohttp_jinja2.template('search.html')
async def handle_search(request):
    # ... (पिछला सर्च हैंडलर कोड) ...

@aiohttp_jinja2.template('watch.html')
async def handle_watch(request):
    # ... (पिछला वॉच हैंडलर कोड) ...

async def health_check(request):
    try:
        if not await request.app['db'].ping():
            return web.Response(text="DB Connection Failed", status=500)
        return web.Response(text="OK", status=200)
    except Exception as e:
        return web.Response(text=f"Error: {e}", status=500)
