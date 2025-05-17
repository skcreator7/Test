from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader
import logging
import re
from config import Config

logger = logging.getLogger(__name__)

def create_app(db, bot):
    app = web.Application()
    setup_jinja2(app, loader=FileSystemLoader('templates'))
    
    app['db'] = db
    app['bot'] = bot
    
    # Setup routes
    app.router.add_get('/', home)
    app.router.add_get('/search', search)
    app.router.add_get('/view/{post_id}', view_post)
    app.router.add_static('/static/', path='static')
    
    # Add error middleware
    async def error_middleware(app, handler):
        async def middleware_handler(request):
            try:
                response = await handler(request)
                return response
            except web.HTTPException as ex:
                raise ex
            except Exception as ex:
                logger.error(f"Error handling request: {ex}")
                return web.Response(text=str(ex), status=500)
        return middleware_handler
    
    app.middlewares.append(error_middleware)
    
    return app

async def fetch_posts(bot, query: str = "", limit: int = 20):
    try:
        results = []
        async for msg in bot.app.search_messages(
            chat_id=Config.SOURCE_CHANNEL_ID,
            query=query,
            limit=limit
        ):
            if msg.text:
                lines = [line.strip() for line in msg.text.split('\n') if line.strip()]
                if lines:
                    post = {
                        'id': msg.id,
                        'title': lines[0],
                        'text': msg.text,
                        'has_episodes': any('episode' in line.lower() for line in lines)
                    }
                    results.append(post)
        return results
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        return []

async def parse_post(text: str):
    try:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return {}
        
        post = {'title': lines[0], 'links': {}, 'episodes': {}}
        current_episode = None
        
        for line in lines[1:]:
            # Check for episode markers
            episode_match = re.match(r'^(Episode|EP)\s*(\d+)', line, re.IGNORECASE)
            if episode_match:
                current_episode = episode_match.group(2)
                post['episodes'][current_episode] = {}
                continue
                
            # Process quality links
            if '🎞️' in line and 'http' in line and 'youtube' not in line.lower():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    quality = parts[0].replace('🎞️', '').strip()
                    url = parts[1].strip()
                    
                    if current_episode:
                        post['episodes'][current_episode][quality] = url
                    else:
                        post['links'][quality] = url
        
        return post
    except Exception as e:
        logger.error(f"Error parsing post: {e}")
        return {}

@template('index.html')
async def home(request):
    return {'title': 'Movie Search Home'}

@template('search.html')
async def search(request):
    try:
        query = request.query.get('q', '').strip()
        posts = await fetch_posts(request.app['bot'], query)
        return {
            'query': query,
            'posts': posts,
            'title': f"Search Results for '{query}'" if query else "Search"
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise web.HTTPInternalServerError()

@template('view.html')
async def view_post(request):
    try:
        post_id = int(request.match_info['post_id'])
        query = request.query.get('q', '')
        
        msg = await request.app['bot'].app.get_messages(
            Config.SOURCE_CHANNEL_ID,
            post_id
        )
        
        if not msg.text:
            raise web.HTTPNotFound()
        
        post_data = await parse_post(msg.text)
        post_data['id'] = post_id
        post_data['query'] = query
        
        return post_data
    except ValueError:
        raise web.HTTPBadRequest()
    except Exception as e:
        logger.error(f"View post error: {e}")
        raise web.HTTPInternalServerError()
