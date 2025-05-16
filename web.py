from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader, select_autoescape
import logging
import re
from config import Config
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def extract_links(text: str) -> List[Dict[str, str]]:
    """Extract and validate streaming links"""
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
            clean_url = url.strip('.,;()[]{}"\'')
            if urlparse(clean_url).scheme in ('http', 'https'):
                links.append({
                    'url': clean_url,
                    'label': label,
                    'host': urlparse(clean_url).netloc
                })
    return links[:15]

@template('watch.html')
async def watch(request: web.Request) -> Dict[str, Any]:
    db = request.app['db']
    bot = request.app['bot']
    post_id = request.query.get('post_id')
    chat_id = request.query.get('chat_id')
    
    post = None
    links = []
    error = None
    
    if post_id and chat_id:
        try:
            # Try database first
            post = await db.posts.find_one({
                "message_id": int(post_id),
                "chat_id": int(chat_id)
            })
            
            # Fetch from Telegram if not in DB or stale
            if not post:
                msg = await bot.app.get_messages(
                    chat_id=int(chat_id),
                    message_ids=int(post_id)
                )
                if msg:
                    post = {
                        "chat_id": msg.chat.id,
                        "message_id": msg.id,
                        "text": msg.text or msg.caption or "",
                        "date": msg.date,
                        "chat_title": msg.chat.title
                    }
                    await db.save_post(post)
            
            if post:
                links = extract_links(post.get('text', ''))
        except Exception as e:
            logger.error(f"Error fetching post: {e}")
            error = "Failed to load post"
    
    return {
        'post': post,
        'links': links,
        'link_count': len(links),
        'error': error,
        'base_url': Config.BASE_URL
    }

def create_app(db, bot) -> web.Application:
    """Create web application with routes"""
    app = web.Application()
    
    # Configure Jinja2
    setup_jinja2(
        app,
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'xml']),
        enable_async=True
    )
    
    # Add routes
    app.add_routes([
        web.get('/watch', watch),
        web.static('/static', 'static')
    ])
    
    # Store dependencies
    app['db'] = db
    app['bot'] = bot
    
    return app
