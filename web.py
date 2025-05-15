from aiohttp import web
from datetime import datetime
from bson import ObjectId
from config import Config
import re

async def handle_watch(request):
    """Single post viewer with smart link labeling"""
    db = request.app['db']
    post_id = request.match_info.get('post_id', '')
    
    try:
        post = await db.get_post(post_id)
        if not post:
            raise web.HTTPNotFound(text="Post not found")

        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"last_accessed": datetime.now()}}
        )
        
        processed_links = []
        links = post.get('links', [])
        
        # Smart labeling logic
        if len(links) > 6:
            # Episode numbering for collections
            for idx, link in enumerate(links, 1):
                processed_links.append({
                    **link,
                    "label": f"Episode {idx}",
                    "quality_class": "episode"
                })
        else:
            # Quality-based labeling
            for link in links:
                quality = str(link.get('quality', 'unknown')).lower()
                quality_class = f"quality-{quality.replace(' ', '-')}"
                
                processed_links.append({
                    **link,
                    "label": link.get('label', 'Open Link'),
                    "quality_class": quality_class
                })

        return {
            'title': post.get('text', '')[:50] or "Private Channel Post",
            'text': post.get('text', ''),
            'links': processed_links
        }
        
    except Exception as e:
        return web.Response(text=f"Error loading post: {str(e)}", status=500)

# [Keep other handlers (handle_index, handle_search, health_check) from previous implementation]
