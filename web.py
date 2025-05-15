from aiohttp import web
import aiohttp_jinja2
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import jinja2

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "your_mongodb_uri")
client = AsyncIOMotorClient(MONGO_URI)
db = client["your_db_name"]

# Aiohttp app and Jinja2 setup
app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))

routes = web.RouteTableDef()

@routes.get("/")
async def handle_home(request):
    return web.Response(text="Working!")

@routes.get("/watch/{post_id}/{title}")
async def handle_watch(request):
    post_id = request.match_info['post_id']

    post = await db.posts.find_one({'_id': ObjectId(post_id)})
    if not post:
        raise web.HTTPNotFound(text="Post not found")

    links = post.get("links", [])

    return aiohttp_jinja2.render_template(
        "watch.html",
        request,
        {
            "post": post,
            "links": links
        }
    )

app.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8000)
