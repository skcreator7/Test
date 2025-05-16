from aiohttp import web
import asyncio

async def health_check(request):
    """Comprehensive health check endpoint"""
    try:
        # Check database connection
        db = request.app['db']
        await db.client.admin.command('ping')
        
        # Check bot connection (if available)
        if 'bot' in request.app:
            if not await request.app['bot'].app.is_connected():
                raise ConnectionError("Bot not connected")
        
        return web.Response(
            text="OK: Database and bot connected",
            status=200,
            content_type='text/plain'
        )
        
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        return web.Response(
            text=f"Service Unavailable: {str(e)}",
            status=503,
            content_type='text/plain'
        )
