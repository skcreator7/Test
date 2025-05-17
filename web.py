from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader
import logging
from config import Config

logger = logging.getLogger(__name__)

async def parse_post(text: str):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return {}
    data = {'title': lines[0], 'links': {}, 'episodes': {}}
    current_ep = None
    for line in lines[1:]:
        if '🎞️' in line and 'http' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                quality = parts[0].replace('🎞️', '').strip()
                url = parts[1].strip()
                if current_ep:
                    data['episodes'][current_ep][quality] = url
                else:
                    data['links'][quality] = url
        elif line.lower().startswith(('episode', 'ep')):
            current_ep = line.split()[1] if len(line.split()) > 1 else "1"
            data['episodes'][current_ep] = {}
    return data

def create_app(db, bot):
    app = web.Application()
    setup_jinja2(app, loader=FileSystemLoader('templates'))
    app['db'] = db
    app['bot'] = bot
    app.router.add_get('/', home)
    app.router.add_get('/search', search)
    app.router.add_get('/view/{post_id}', view_post)
    app.router.add_static('/static/', path='static')
    return app

@template('index.html')
async def home(request):
    return {'title': 'Movie Search'}

@template('search.html')
async def search(request):
    query = request.query.get('q', '').strip()
    posts = []
    async for msg in request.app['bot'].client.iter_messages(
        Config.SOURCE_CHANNEL_ID,
        search=query,
        limit=20
    ):
        if msg.text:
            post = await parse_post(msg.text)
            post['id'] = msg.id
            post['has_episodes'] = bool(post.get('episodes'))
            posts.append(post)
    return {'query': query, 'posts': posts}

@template('view.html')
async def view_post(request):
    post_id = int(request.match_info['post_id'])
    msg = await request.app['bot'].client.get_messages(
        Config.SOURCE_CHANNEL_ID,
        ids=post_id
    )
    if not msg.text:
        raise web.HTTPNotFound()
    post = await parse_post(msg.text)
    post['id'] = post_id
    post['query'] = request.query.get('q', '')
    return post
