from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = "movie_bot"):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.posts = self.db.posts
        logger.info(f"Connected to MongoDB: {db_name}")

    async def initialize(self):
        """Create search indexes with error handling"""
        try:
            # Get current indexes
            current_indexes = await self.posts.index_information()
            
            # Drop existing text indexes if they exist
            for name, index in current_indexes.items():
                if any('text' in str(field) for field in index.get('key', {}).values()):
                    logger.info(f"Dropping existing text index: {name}")
                    await self.posts.drop_index(name)
            
            # Create new indexes
            await self.posts.create_index([("title", TEXT)])
            await self.posts.create_index([("text", TEXT)])
            logger.info("Search indexes created successfully")
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            logger.warning("Continuing without text indexes")

    async def search_posts(self, query: str, limit: int = 10) -> List[Dict]:
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

    async def close(self):
        self.client.close()
