from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, DESCENDING
from typing import List, Dict, Optional
from config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = Config.MONGO_DB):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.posts = self.db.posts

    async def initialize(self):
        """Create indexes"""
        await self.posts.create_index([("text", TEXT)])
        await self.posts.create_index([("date", DESCENDING)])
        logger.info("Database indexes created")

    async def get_post(self, post_id: str) -> Optional[Dict]:
        """Get single post by ID"""
        return await self.posts.find_one({"_id": post_id})

    async def search_posts(self, query: str, limit: int = 10) -> List[Dict]:
        """Search posts with text matching"""
        cursor = self.posts.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        return await cursor.to_list(length=limit)

    async def save_post(self, post_data: Dict) -> bool:
        """Save post to database"""
        try:
            await self.posts.insert_one(post_data)
            return True
        except Exception as e:
            logger.error(f"Error saving post: {e}")
            return False
