from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, DESCENDING
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = "movie_bot"):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.movies = self.db.movies  # Changed from posts to movies
        logger.info(f"Connected to MongoDB: {db_name}")

    async def initialize(self):
        """Create search indexes"""
        try:
            await self.movies.create_index([("title", TEXT)])
            await self.movies.create_index([("plot", TEXT)])
            logger.info("Search indexes created")
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            raise

    async def search_movies(self, query: str, limit: int = 5) -> List[Dict]:
        """Search movies with text matching"""
        try:
            cursor = self.movies.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def close(self):
        self.client.close()
