from aiohttp import web
from datetime import datetime
from bson import ObjectId
from config import Config, WarningLevel

async def handle_index(request):
    return web.Response(
        text="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram Bot</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #333; }
                .search-box { margin: 20px auto; max-width: 500px; }
                input { width: 70%; padding: 10px; }
                button { padding: 10px 20px; background: #0088cc; color: white; border: none; }
            </style>
        </head>
        <body>
            <h1>Telegram Search Bot</h1>
            <p>Search across Telegram channels for content</p>
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
        <h1>Results for "{query}"</h1>
        {"".join(
            f'''
            <div class="result">
                <h3>{result.get('chat_title', 'Unknown Channel')}</h3>
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
    
    title = post.get('chat_title', 'Unknown') + " - " + post.get('text', '')[:50]
    links = post.get('links', [])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta property="og:title" content="{title}">
        <meta property="og:description" content="Download links from Telegram">
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{ 
                color: #333; 
                font-size: 1.5em;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            .post-text {{
                margin: 15px 0;
                padding: 10px;
                background: #f9f9f9;
                border-radius: 4px;
            }}
            .links-container {{
                margin-top: 20px;
            }}
            .link-btn {{
                display: inline-block;
                margin: 10px;
                padding: 12px 20px;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                min-width: 120px;
                text-align: center;
                transition: transform 0.2s;
            }}
            .link-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .quality-720p {{ background: #4CAF50; }}
            .quality-1080p {{ background: #2196F3; }}
            .quality-4K {{ background: #9C27B0; }}
            .quality-unknown {{ background: #607D8B; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <div class="post-text">{post.get('text', '')}</div>
            <div class="links-container">
                {"".join(
                    f'<a href="{link["url"]}" class="link-btn quality-{link["quality"]}" target="_blank">{link["label"]}</a>'
                    for link in links
                )}
            </div>
        </div>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")

async def handle_admin(request):
    if request.query.get('key') != Config.SECRET_KEY:
        raise web.HTTPUnauthorized()
    
    return web.Response(
        text="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .menu { margin-bottom: 20px; }
                .menu a { margin-right: 15px; text-decoration: none; }
            </style>
        </head>
        <body>
            <h1>Admin Panel</h1>
            <div class="menu">
                <a href="/warnings?key=SECRET_KEY">View Warnings</a>
                <a href="/message_logs?key=SECRET_KEY">Message Logs</a>
            </div>
            <p>Replace SECRET_KEY with your actual key in the URLs</p>
        </body>
        </html>
        """.replace("SECRET_KEY", Config.SECRET_KEY),
        content_type="text/html"
    )

async def handle_warnings(request):
    db = request.app['db']
    if request.query.get('key') != Config.SECRET_KEY:
        raise web.HTTPUnauthorized()
    
    chat_id = request.query.get('chat_id')
    user_id = request.query.get('user_id')
    
    if chat_id and user_id:
        count, warnings = await db.get_warning_count(int(chat_id), int(user_id))
        html = f"""
        <h2>Warnings for user {user_id} in chat {chat_id}</h2>
        <p>Total active warnings: {count}</p>
        <table>
            <tr><th>Reason</th><th>Level</th><th>Time</th><th>Expires</th></tr>
            {"".join(
                f"<tr><td>{w['reason']}</td><td>{WarningLevel(w['level']).name}</td>"
                f"<td>{w['timestamp'].strftime('%Y-%m-%d %H:%M')}</td>"
                f"<td>{w['expires_at'].strftime('%Y-%m-%d %H:%M')}</td></tr>"
                for w in warnings
            )}
        </table>
        """
    else:
        warnings = await db.warnings.find({
            "expires_at": {"$gt": datetime.now()}
        }).sort("timestamp", -1).limit(100).to_list(None)
        
        html = """
        <h2>All Active Warnings</h2>
        <table>
            <tr><th>Chat ID</th><th>User ID</th><th>Reason</th><th>Level</th><th>Time</th></tr>
            {"".join(
                f"<tr><td>{w['chat_id']}</td><td>{w['user_id']}</td>"
                f"<td>{w['reason']}</td><td>{WarningLevel(w['level']).name}</td>"
                f"<td>{w['timestamp'].strftime('%Y-%m-%d %H:%M')}</td></tr>"
                for w in warnings
            )}
        </table>
        """
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Warning Tracker</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 8px; border: 1px solid #ddd; text-align: left; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .WARNING {{ color: orange; font-weight: bold; }}
            .SEVERE {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """
    
    return web.Response(text=full_html, content_type="text/html")

async def health_check(request):
    return web.json_response({
        "status": "ok",
        "time": datetime.now().isoformat(),
        "service": "Telegram Bot",
        "version": "1.0"
    })
