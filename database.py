from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from pymongo import TEXT
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[Config.DB_NAME]
        self.posts = self.db.posts

    async def initialize(self):
        """Create indexes"""
        try:
            await self.posts.create_index([("text", TEXT)])
            logger.info("Database indexes created")
        except Exception as e:
            logger.error(f"Index creation failed: {e}")

    async def save_post(self, post_data):
        """Save post with duplicate check"""
        try:
            existing = await self.posts.find_one({
                "chat_id": post_data["chat_id"],
                "message_id": post_data["message_id"]
            })
            if not existing:
                await self.posts.insert_one(post_data)
                return True
            return False
        except Exception as e:
            logger.error(f"Save post error: {e}")
            return False

    async def search_posts(self, query, limit=5):
        """Full-text search"""
        try:
            cursor = self.posts.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
