from aiohttp import web
from datetime import datetime
from bson import ObjectId
from config import Config

async def handle_index(request):
    """Homepage with search form"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Post Viewer</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: auto; }
            .search-box { padding: 10px; width: 300px; margin: 20px 0; }
            .btn { padding: 10px 15px; background: #007bff; color: white; border: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>Welcome to Telegram Post Search</h1>
        <form action="/search" method="get">
            <input type="text" name="query" class="search-box" placeholder="Search posts..." required>
            <button type="submit" class="btn">Search</button>
        </form>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

async def handle_search(request):
    """Search results handler"""
    db = request.app['db']
    query = request.query.get('query', '').strip()
    
    if not query:
        raise web.HTTPBadRequest(text="Missing search query")
    
    results = await db.search_posts(query)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: auto; }}
            .result {{ margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }}
            .result a {{ color: #007bff; text-decoration: none; }}
        </style>
    </head>
    <body>
        <h1>Results for "{query}"</h1>
        <div class="results">
            {"".join(f'''
            <div class="result">
                <p>{result.get('text', 'No text')[:200]}...</p>
                <a href="/watch/{result["_id"]}">View Full Post</a>
            </div>
            ''' for result in results)}
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

async def handle_watch(request):
    """Single post viewer"""
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
    
    link_buttons = ''
    for link in links:
        quality = link.get('quality', 'default').lower()
        color_map = {
            '1080p': 'blue',
            '720p': 'green',
            '480p': 'orange',
            '360p': 'red'
        }
        quality_color = color_map.get(quality, 'default')
        
        link_buttons += f'''
        <a href="{link['url']}" class="btn {quality_color}">
            {link['label']} ({quality})
        </a><br>
        '''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: auto; }}
            .btn {{
                display: inline-block;
                padding: 10px 15px;
                margin: 5px 0;
                text-decoration: none;
                color: white;
                border-radius: 5px;
            }}
            .blue {{ background-color: #007BFF; }}
            .green {{ background-color: #28A745; }}
            .orange {{ background-color: #FD7E14; }}
            .red {{ background-color: #DC3545; }}
            .default {{ background-color: #6C757D; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <p>{post.get('text', '')}</p>
        <div class="links">{link_buttons}</div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

async def health_check(request):
    """Health check endpoint"""
    return web.Response(text="OK", status=200)
