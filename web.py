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
    
    # Update last accessed time
    await db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"last_accessed": datetime.now()}}
    )
    
    title = post.get('text', '')[:100].replace('"', "'") or "Channel Post"
    links = post.get('links', [])
    
    # Generate link HTML with proper attributes
    link_html = ""
    for link in links:
        link_html += f"""
        <div class="link-container">
            <a href="{link['url']}" 
               class="link-btn quality-{link['quality']}" 
               target="_blank"
               rel="noopener noreferrer">
                {link['label']}
            </a>
            <div class="link-meta">
                <span class="link-url">{link['url'][:50]}...</span>
                <button class="copy-btn" data-url="{link['url']}">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta property="og:title" content="{title}">
        <meta property="og:description" content="View links from Telegram post">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f7fa;
                color: #333;
            }}
            .container {{
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                font-size: 1.4em;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }}
            .post-content {{
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                white-space: pre-wrap;
                line-height: 1.6;
            }}
            .links-container {{
                margin-top: 30px;
            }}
            .link-container {{
                margin-bottom: 15px;
            }}
            .link-btn {{
                display: inline-block;
                padding: 12px 25px;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                min-width: 140px;
                text-align: center;
                transition: all 0.2s;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .link-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }}
            .quality-720p {{ background: #27ae60; }}
            .quality-1080p {{ background: #2980b9; }}
            .quality-4K {{ background: #8e44ad; }}
            .quality-unknown {{ background: #7f8c8d; }}
            .link-meta {{
                display: flex;
                align-items: center;
                margin-top: 8px;
                font-size: 0.9em;
            }}
            .link-url {{
                color: #7f8c8d;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                flex-grow: 1;
            }}
            .copy-btn {{
                background: none;
                border: none;
                color: #7f8c8d;
                cursor: pointer;
                padding: 5px;
                margin-left: 10px;
            }}
            .copy-btn:hover {{
                color: #3498db;
            }}
            @media (max-width: 600px) {{
                .container {{
                    padding: 15px;
                }}
                .link-btn {{
                    width: 100%;
                    display: block;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Post Links</h1>
            <div class="post-content">{post.get('text', 'No content')}</div>
            <div class="links-container">
                {link_html}
            </div>
        </div>
        
        <script>
            document.querySelectorAll('.copy-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    const url = btn.getAttribute('data-url');
                    navigator.clipboard.writeText(url).then(() => {{
                        const originalIcon = btn.innerHTML;
                        btn.innerHTML = '<i class="fas fa-check"></i>';
                        setTimeout(() => {{
                            btn.innerHTML = originalIcon;
                        }}, 2000);
                    }});
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")
