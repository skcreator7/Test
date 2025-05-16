from aiohttp import web
from aiohttp_jinja2 import template, setup as setup_jinja2
from jinja2 import FileSystemLoader, select_autoescape
import logging
import re
from config import Config
from typing import List, Dict, Optional, Any
from pyrogram.types import InputPeerChannel
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def extract_links(text: str) -> List[Dict[str, str]]:
    """
    Extract and categorize streaming links from text with enhanced validation
    
    Args:
        text: The text content to search for links
        
    Returns:
        List of dictionaries containing validated links with quality labels
    """
    patterns = [
        (r'(?:480p|SD).*?(http[^\s]+)', '480p'),
        (r'(?:720p\s*HEVC|x265).*?(http[^\s]+)', '720p HEVC'),
        (r'720p.*?(http[^\s]+)', '720p'),
        (r'(?:1080p|FHD).*?(http[^\s]+)', '1080p'),
        (r'(?:Episode\s+\d+|EP\s*\d+).*?(http[^\s]+)', 'Episode'),
        (r'(?:4K|2160p|UHD).*?(http[^\s]+)', '4K UHD')
    ]
    
    links = []
    seen_urls = set()
    
    for pattern, label in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for url in matches:
            # Clean URL and validate
            clean_url = url.strip('.,;()[]{}"\'')
            if clean_url not in seen_urls and is_valid_url(clean_url):
                links.append({
                    'url': clean_url,
                    'label': label,
                    'host': urlparse(clean_url).netloc
                })
                seen_urls.add(clean_url)
    
    return links[:15]  # Increased limit with deduplication

@template('watch.html')
async def watch(request: web.Request) -> Dict[str, Any]:
    """
    Handle watch page requests with enhanced caching and fallback logic
    
    Args:
        request: The incoming web request
        
    Returns:
        Context dictionary for template rendering
    """
    db = request.app['db']
    bot = request.app['bot']
    post_id = request.query.get('post_id')
    chat_id = request.query.get('chat_id')
    
    post = None
    links = []
    error = None
    
    if not post_id or not chat_id:
        error = "Missing post_id or chat_id parameters"
    else:
        try:
            # Try to get from database first
            post = await db.posts.find_one({
                "message_id": int(post_id),
                "chat_id": int(chat_id)
            })
            
            # If not in DB or older than 1 day, fetch from Telegram
            if not post or (post.get('date') and 
                          (datetime.utcnow() - post['date']).days > 1):
                try:
                    channel = await bot._get_channel_peer(int(chat_id))
                    msg = await bot.app.get_messages(
                        entity=channel,
                        message_ids=int(post_id)
                    )
                    
                    if msg:
                        post = {
                            "chat_id": msg.chat.id,
                            "message_id": msg.id,
                            "text": msg.text or msg.caption or "",
                            "date": msg.date,
                            "chat_title": msg.chat.title,
                            "last_updated": datetime.utcnow()
                        }
                        # Update or insert with atomic operation
                        await db.posts.update_one(
                            {
                                "message_id": int(post_id),
                                "chat_id": int(chat_id)
                            },
                            {"$set": post},
                            upsert=True
                        )
                except Exception as fetch_error:
                    logger.error(f"Telegram fetch error: {fetch_error}")
                    if not post:  # Only error if we have no cached version
                        error = "Failed to fetch post from Telegram"
            
            if post:
                links = extract_links(post.get('text', ''))
                if not links:
                    error = "No valid streaming links found"
        except ValueError as ve:
            error = "Invalid post_id or chat_id format"
            logger.error(f"Value error: {ve}")
        except Exception as e:
            error = "An error occurred while processing your request"
            logger.error(f"Watch handler error: {e}", exc_info=True)
    
    return {
        'post': post,
        'links': links,
        'link_count': len(links),
        'error': error,
        'base_url': Config.BASE_URL
    }

def create_app(db, bot) -> web.Application:
    """Configure and return the web application with enhanced settings"""
    app = web.Application()
    
    # Configure Jinja2 templates
    setup_jinja2(
        app,
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'xml']),
        enable_async=True
    )
    
    # Add routes
    app.add_routes([
        web.get('/watch', watch),
        web.static('/static', 'static', follow_symlinks=True)
    ])
    
    # Store dependencies
    app['db'] = db
    app['bot'] = bot
    
    # Add error handlers
    async def handle_404(request):
        return web.json_response({'error': 'Not found'}, status=404)
    
    async def handle_500(request):
        return web.json_response({'error': 'Server error'}, status=500)
    
    app.middlewares.append(error_middleware)
    
    return app

@web.middleware
async def error_middleware(request, handler):
    """Global error handling middleware"""
    try:
        response = await handler(request)
        if response.status != 404:
            return response
        message = response.message
    except web.HTTPException as ex:
        if ex.status != 404:
            raise
        message = ex.reason
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return web.json_response(
            {'error': 'Internal server error'},
            status=500
        )
    
    return web.json_response({'error': message}, status=404)
