from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader, select_autoescape
import logging
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def setup_routes(app):
    """Configure all application routes"""
    # Static files
    static_dir = Path(__file__).parent / 'static'
    app.router.add_static('/static/', path=static_dir, name='static')
    
    # Web routes
    app.router.add_get('/', home)
    app.router.add_get('/watch', watch_handler)

def setup_jinja2_templates(app):
    """Configure Jinja2 templates"""
    templates_dir = Path(__file__).parent / 'templates'
    setup_jinja2(
        app,
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(['html', 'xml']),
        enable_async=True
    )

async def home(request):
    """Home page handler"""
    return web.Response(text="Welcome to Movie Bot")

@template('watch.html')
async def watch_handler(request):
    """Watch page handler"""
    db = request.app['db']
    bot = request.app['bot']
    
    post_id = request.query.get('post_id')
    chat_id = request.query.get('chat_id')
    
    context = {
        'post': None,
        'links': [],
        'error': None
    }
    
    if post_id and chat_id:
        try:
            # Try to get post from database
            post = await db.posts.find_one({
                "message_id": int(post_id),
                "chat_id": int(chat_id)
            })
            
            if post:
                context['post'] = post
                context['links'] = extract_links(post.get('text', ''))
        except Exception as e:
            logger.error(f"Error fetching post: {e}")
            context['error'] = "Failed to load post"
    
    return context

def extract_links(text: str) -> List[Dict[str, str]]:
    """Extract streaming links from text"""
    if not text:
        return []
    
    patterns = [
        (r'(?:480p|SD).*?(http[^\s]+)', '480p'),
        (r'(?:720p\s*HEVC|x265).*?(http[^\s]+)', '720p HEVC'),
        (r'720p.*?(http[^\s]+)', '720p'),
        (r'(?:1080p|FHD).*?(http[^\s]+)', '1080p'),
        (r'(?:4K|2160p|UHD).*?(http[^\s]+)', '4K UHD')
    ]
    
    links = []
    for pattern, label in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for url in matches:
            links.append({
                'url': url.strip('.,;()[]{}"\''),
                'label': label
            })
    
    return links[:15]

def create_app(db, bot) -> web.Application:
    """Application factory"""
    app = web.Application()
    
    # Setup templates
    setup_jinja2_templates(app)
    
    # Setup routes
    setup_routes(app)
    
    # Store dependencies
    app['db'] = db
    app['bot'] = bot
    
    return app
