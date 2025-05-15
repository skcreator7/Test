from aiohttp import web
from bson import ObjectId

async def health_check(request):
    try:
        await request.app['db'].client.admin.command('ping')
        return web.Response(text="OK")
    except Exception:
        return web.Response(status=500)
