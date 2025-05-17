from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = "movie_bot"):
        self.client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000
        )
        self.db = self.client[db_name]
        self.posts = self.db.posts
        self.channels = self.db.channels

    async def initialize(self) -> None:
        try:
            indexes = await self.posts.index_information()
            if "text_title_text" not in indexes:
                await self.posts.create_index(
                    [("text", TEXT), ("title", TEXT)],
                    name="text_title_text",
                    background=True
                )
                logger.info("Created text index")
            if "channels" not in await self.db.list_collection_names():
                await self.db.create_collection("channels")
                await self.channels.create_index([("_id", 1)])
                logger.info("Created channels collection")
        except Exception as e:
            logger.error(f"Database init failed: {e}")
            raise

    async def close(self):
        self.client.close()

    async def save_post(self, post):
        await self.posts.update_one(
            {"_id": post["_id"]},
            {"$set": post},
            upsert=True
        )

    async def delete_post(self, post_id):
        await self.posts.delete_one({"_id": post_id})

    async def search_posts(self, query: str, limit: int = 5):
        cursor = self.posts.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}, "title": 1, "_id": 1, "text": 1}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        results = []
        async for doc in cursor:
            title = doc.get("title") or "No Title"
            results.append({"_id": doc["_id"], "title": title, "text": doc.get("text", "")})
        return results
