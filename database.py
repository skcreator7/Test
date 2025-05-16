import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, DESCENDING
from typing import List, Dict, Optional, Any  # Added type imports
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
        self._initialized = False

    async def initialize(self) -> None:
        """Create indexes if not already initialized"""
        if self._initialized:
            return
            
        try:
            # Test connection first
            await self.client.admin.command('ping')
            
            # Create indexes in parallel
            await asyncio.gather(
                self.posts.create_index([("text", TEXT)]),
                self.posts.create_index([("message_id", DESCENDING)]),
                self.posts.create_index([("chat_id", DESCENDING)]),
                self.posts.create_index([("date", DESCENDING)])
            )
            self._initialized = True
            logger.info("Database initialized with indexes")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def save_post(self, post_data: Dict[str, Any]) -> bool:
        """Upsert a post with timestamp"""
        try:
            if 'created_at' not in post_data:
                post_data['created_at'] = datetime.utcnow()
                
            result = await self.posts.update_one(
                {
                    "message_id": post_data["message_id"],
                    "chat_id": post_data["chat_id"]
                },
                {"$set": post_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Failed to save post: {e}")
            return False

    async def close(self) -> None:
        """Close connection safely"""
        try:
            self.client.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
