from aiohttp import web
import os
from pathlib import Path

def setup_routes(app):
    # Static files
    static_dir = Path(__file__).parent / 'static'
    app.router.add_static('/static/', path=static_dir, name='static')
    
    # Templates
    @app.get('/')
    async def home(request):
        return web.Response(text="Welcome to Movie Bot")
    
    @app.get('/watch')
    async def watch(request):
        # Your watch handler logic
        return web.json_response({...})
