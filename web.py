from aiohttp import web
from datetime import datetime
from bson import ObjectId
import aiohttp_jinja2

async def handle_watch(request):
    """Render single post with smart link labeling."""
    db = request.app['db']
    post_id = request.match_info.get('post_id')

    if not ObjectId.is_valid(post_id):
        raise web.HTTPBadRequest(text="Invalid post ID")

    post = await db.get_post(post_id)
    if not post:
        raise web.HTTPNotFound(text="Post not found")

    await db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"last_accessed": datetime.now()}}
    )

    links = post.get('links', [])
    processed_links = []

    if len(links) > 5:
        # Episode labeling
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
            label = link.get('label') or quality.upper() or "Open Link"

            processed_links.append({
                **link,
                "label": label,
                "quality_class": quality_class
            })

    return aiohttp_jinja2.render_template(
        "watch.html", request, {
            "title": post.get("text", "")[:50] or "Post View",
            "text": post.get("text", ""),
            "links": processed_links
        }
    )


# Placeholder handlers (optional)
async def handle_index(request):
    return web.Response(text="Index")

async def handle_search(request):
    return web.Response(text="Search")

async def health_check(request):
    return web.Response(text="OK")
