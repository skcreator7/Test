from aiohttp import web
import jinja2
import aiohttp_jinja2

def setup_static_routes(app):
    app.router.add_static('/static/', path='static', name='static')

def create_app(db, bot=None):
    app = web.Application()
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader('templates'),
        context_processors=[aiohttp_jinja2.request_processor]
    )
    setup_static_routes(app)

    @aiohttp_jinja2.template('search.html')
    async def search(request):
        q = request.query.get('q', '').strip()
        results = []
        if q:
            results = await db.search_posts(q)
            # Direct post open if only one search result
            if len(results) == 1:
                raise web.HTTPFound(request.app.router['post_page'].url_for(id=str(results[0]['_id'])))
        return {'results': results, 'title': 'Search', 'request': request}

    @aiohttp_jinja2.template('post.html')
    async def post_page(request):
        post_id = request.match_info['id']
        post = await db.posts.find_one({"_id": post_id})
        if not post:
            raise web.HTTPNotFound()
        return {'post': post, 'title': post.get('title', ''), 'request': request}

    app.router.add_get('/', search, name='search')
    app.router.add_get('/post/{id}', post_page, name='post_page')
    return app
