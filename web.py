import aiohttp_jinja2
from aiohttp import web
from jinja2 import FileSystemLoader
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


def create_app(db, bot):
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=FileSystemLoader("templates"))
    app["db"] = db
    app["bot"] = bot

    app.router.add_get("/", index)
    app.router.add_get("/search", search_handler)
    app.router.add_get("/watch/{post_id}/{title}", watch_handler)
    app.router.add_static("/static/", path="static", name="static")

    return app


@aiohttp_jinja2.template("index.html")
async def index(request):
    return {"title": "Movie Bot"}


@aiohttp_jinja2.template("search.html")
async def search_handler(request):
    query = request.rel_url.query.get("q", "").strip()
    if not query:
        return {"query": "", "results": []}

    db = request.app["db"]
    cursor = db.posts.find({"$text": {"$search": query}}).sort(
        [("score", {"$meta": "textScore"})]
    ).limit(10)

    results = []
    async for doc in cursor:
        results.append({
            "title": doc.get("title", "Untitled"),
            "url": f"/watch/{doc['_id']}/{doc.get('title', 'watch').replace(' ', '-')}"
        })

    return {"query": query, "results": results}


@aiohttp_jinja2.template("watch.html")
async def watch_handler(request):
    post_id = request.match_info.get("post_id")
    db = request.app["db"]

    try:
        post = await db.posts.find_one({"_id": ObjectId(post_id)})
    except Exception:
        post = None

    if not post:
        raise web.HTTPNotFound()

    links = post.get("links", [])
    buttons = []

    if len(links) <= 3:
        # show by quality
        buttons = [{"label": link["label"], "url": link["url"]} for link in links]
    else:
        # show as episodes
        buttons = [
            {"label": f"Episode {i+1}", "url": link["url"]} for i, link in enumerate(links)
        ]

    return {
        "title": post.get("title", "Watch Now"),
        "links": buttons,
        "post": post
    }
