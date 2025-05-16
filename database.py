from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri):
        self.client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        self.db = self.client.get_default_database()
        self.posts = self.db.posts

    async def initialize(self):
        """Initialize with proper error handling"""
        try:
            await self.posts.create_index([("text", TEXT)])
            logger.info("Database indexes created")
        except Exception as e:
            logger.error(f"Index creation error: {e}")
            raise

    async def search_posts(self, query, limit=5):
        """Thread-safe search implementation"""
        try:
            cursor = self.posts.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
