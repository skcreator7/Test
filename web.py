from aiohttp import web
from datetime import datetime
from bson import ObjectId
from config import Config

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
    
    # Generate link buttons with quality-based color coding
    link_buttons = ''
    for link in links:
        quality = 'default'
        if '1080' in link:
            quality = 'blue'
        elif '720' in link:
            quality = 'green'
        elif '480' in link:
            quality = 'orange'
        elif '360' in link:
            quality = 'red'
        link_buttons += f'<a href="{link}" class="btn {quality}">{link}</a><br>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
                max-width: 800px;
                margin: auto;
            }}
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
            @media (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .btn {{
                    width: 100%;
                    box-sizing: border-box;
                }}
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <p>{post.get('text', '')}</p>
        <div>
            {link_buttons}
        </div>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")
