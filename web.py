from aiohttp import web
from datetime import datetime
from bson import ObjectId
from config import Config

async def handle_index(request):
    """Handle root route (/) with basic welcome page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telegram Post Viewer</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: auto; }
            .search-box { padding: 10px; width: 300px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>Welcome to Telegram Post Search</h1>
        <form action="/search" method="get">
            <input type="text" name="query" class="search-box" placeholder="Search posts...">
            <button type="submit">Search</button>
        </form>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

async def handle_search(request):
    """Handle search requests"""
    db = request.app['db']
    query = request.query.get('query', '')
    
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
            .result {{ margin: 15px 0; padding: 10px; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <h1>Search Results for "{query}"</h1>
        <div class="results">
            {"".join(f'<div class="result"><p>{result["text"][:200]}...</p><a href="/watch/{result["_id"]}">View Post</a></div>' for result in results)}
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

async def handle_watch(request):
    # [Keep your existing handle_watch code here]
    # ... (your original handle_watch implementation)
