from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
import jinja2
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_routes(app, db, bot):
    @app.get('/')
    @template('watch.html')
    async def index(request):
        return {'title': 'Telegram Search Bot'}

    @app.get('/watch')
