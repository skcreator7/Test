from aiohttp import web

async def health_check(request):
    try:
        # Check both web server and database
        await request.app['db'].client.admin.command('ping')
        return web.Response(text="OK", status=200)
    except Exception as e:
        print(f"Health check failed: {e}")
        return web.Response(text="Service Unavailable", status=503)
