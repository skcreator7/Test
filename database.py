from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
import logging
from config import Config

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
        """Initialize database with proper indexes"""
        try:
            # Create text index if not exists
            indexes = await self.posts.index_information()
            if "text_title_text" not in indexes:
                await self.posts.create_index(
                    [("text", TEXT), ("title", TEXT)],
                    name="text_title_text",
                    background=True
                )
                logger.info("Created text index")

            # Ensure channels collection exists
            if "channels" not in await self.db.list_collection_names():
                await self.db.create_collection("channels")
                await self.channels.create_index([("_id", 1)])
                logger.info("Created channels collection")

        except Exception as e:
            logger.error(f"Database init failed: {e}")
            raise

    async def close(self):
        """Close MongoDB connection"""
        await self.client.close()
