from aiohttp import web
from datetime import datetime
from bson import ObjectId
from config import Config

async def handle_index(request):
    return web.Response(
        text="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Private Channel Archive</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #333; }
                .search-box { margin: 20px auto; max-width: 500px; }
                input { width: 70%; padding: 10px; }
                button { padding: 10px 20px; background: #0088cc; color: white; border: none; }
            </style>
        </head>
        <body>
            <h1>Private Channel Archive</h1>
            <p>Search posts from the private channel</p>
            <div class="search-box">
                <form action="/search" method="get">
                    <input type="text" name="q" placeholder="Search query...">
                    <button type="submit">Search</button>
                </form>
            </div>
        </body>
        </html>
        """,
        content_type="text/html"
    )

async def handle_search(request):
    db = request.app['db']
    query = request.query.get('q', '').strip()
    
    if not query:
        raise web.HTTPFound('/')
    
    results = await db.search_posts(query)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .result {{ margin-bottom: 20px; padding: 15px; border: 1px solid #eee; border-radius: 5px; }}
            .view-link {{ color: #0088cc; text-decoration: none; }}
        </style>
    </head>
    <body>
        <h1>Results from private channel</h1>
        {"".join(
            f'''
            <div class="result">
                <p>{result.get('text', '')[:200]}...</p>
                <a href="/watch/{result['_id']}" class="view-link">View Links</a>
            </div>
            '''
            for result in results
        )}
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")

async def handle_watch(request):
    db = request.app['db']
    post_id = request.match_info.get('post_id', '')
    
    post = await db.get_post(post_id)
    if not post:
        raise web.HTTPNotFound(text="Post not found")
    
    await db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"last_accessed": datetime.now()}}
    )
    
    title = post.get('text', '')[:50] or "Private Channel Post"
    links = post.get('links', [])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <!-- ... (keep existing watch.html template from previous implementation) ... -->
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")

async def health_check(request):
    return web.json_response({
        "status": "ok",
        "time": datetime.now().isoformat(),
        "service": "Private Channel Archive",
        "version": "1.0"
    })
