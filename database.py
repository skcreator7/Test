from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, DESCENDING
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = "movie_bot"):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.posts = self.db.posts
        logger.info(f"Connected to MongoDB database: {db_name}")

    async def initialize(self):
        """Create indexes"""
        try:
            await self.posts.create_index([("text", TEXT)])
            await self.posts.create_index([("date", DESCENDING)])
            logger.info("Database indexes created")
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            raise

    async def close(self):
        """Close connection"""
        self.client.close()
        logger.info("Database connection closed")
