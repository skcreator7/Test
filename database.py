from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
from pyrogram import raw
import logging
from typing import Dict, List, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = "movie_bot") -> None:
        """
        Initialize MongoDB connection
        Args:
            uri: MongoDB connection string
            db_name: Database name (default: 'movie_bot')
        """
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        self.posts = self.db.posts
        self.channels = self.db.channels
        logger.info(f"Connected to MongoDB: {db_name}")

    async def initialize(self) -> None:
        """Initialize database indexes and collections"""
        try:
            # Create text indexes if they don't exist
            if 'title_text' not in await self.posts.index_information():
                await self.posts.create_index([("title", TEXT)])
                await self.posts.create_index([("text", TEXT)])
                logger.info("Created text search indexes")

            # Ensure channels collection exists
            if "channels" not in await self.db.list_collection_names():
                await self.db.create_collection("channels")
                logger.info("Created channels collection")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def update_channel_hash(self, channel_id: int, access_hash: int) -> None:
        """
        Update channel access hash in database
        Args:
            channel_id: Telegram channel ID
            access_hash: Channel access hash
        """
        try:
            await self.channels.update_one(
                {'_id': channel_id},
                {'$set': {'access_hash': access_hash}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Failed to update channel hash: {e}")
            raise

    async def get_channel_peer(self, bot: Any) -> raw.types.InputPeerChannel:
        """
        Get InputPeerChannel for the source channel
        Args:
            bot: TelegramBot instance
        Returns:
            InputPeerChannel object
        """
        try:
            # Try to get fresh channel info first
            chat = await bot.app.get_chat(Config.SOURCE_CHANNEL_ID)
            await self.update_channel_hash(chat.id, chat.access_hash)
            return raw.types.InputPeerChannel(
                channel_id=chat.id,
                access_hash=chat.access_hash
            )
        except Exception as e:
            logger.warning(f"Failed to get fresh channel info: {e}, trying cache")
            # Fallback to cached data
            doc = await self.channels.find_one({'_id': Config.SOURCE_CHANNEL_ID})
            if doc and doc.get('access_hash'):
                return raw.types.InputPeerChannel(
                    channel_id=doc['_id'],
                    access_hash=doc['access_hash']
                )
            logger.error("No channel info available")
            raise ValueError("Channel information not available")

    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search posts using MongoDB text search
        Args:
            query: Search query string
            limit: Maximum results to return (default: 10)
        Returns:
            List of matching posts
        """
        try:
            cursor = self.posts.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

    async def close(self) -> None:
        """Cleanly close database connection"""
        try:
            await self.client.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
