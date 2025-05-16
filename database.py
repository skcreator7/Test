from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, DESCENDING
import logging
from typing import List, Dict, Optional, Any
from bson import ObjectId
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = Config.MONGO_DB):
        self.client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )
        self.db = self.client[db_name]
        self.posts = self.db.posts

    async def initialize(self) -> None:
        """Create indexes"""
        try:
            await asyncio.gather(
                self.posts.create_index([("text", TEXT)]),
                self.posts.create_index([("message_id", DESCENDING)]),
                self.posts.create_index([("chat_id", DESCENDING)])
            )
            logger.info("Database indexes created")
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            raise

    async def save_post(self, post_data: Dict[str, Any]) -> bool:
        """Upsert a post"""
        try:
            await self.posts.update_one(
                {
                    "message_id": post_data["message_id"],
                    "chat_id": post_data["chat_id"]
                },
                {"$set": post_data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Save post error: {e}")
            return False

    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search posts with text matching"""
        try:
            cursor = self.posts.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def close(self) -> None:
        """Close connections"""
        self.client.close()
