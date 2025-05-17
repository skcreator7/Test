from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
from pyrogram import raw
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = "movie_bot") -> None:
        """
        Initialize MongoDB connection with enhanced settings
        Args:
            uri: MongoDB connection string
            db_name: Database name (default: 'movie_bot')
        """
        self.client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=30000,
            connectTimeoutMS=10000,
            retryWrites=True,
            replicaSet='atlas-yg410i-shard-0'  # From your logs
        )
        self.db = self.client[db_name]
        self.posts = self.db.posts
        self.channels = self.db.channels
        logger.info(f"Connected to MongoDB cluster: {self.client.address}")

    async def initialize(self) -> None:
        """Initialize database with proper index handling"""
        try:
            # Check existing indexes
            existing_indexes = await self.posts.index_information()
            logger.debug(f"Existing indexes: {list(existing_indexes.keys())}")

            # Create text index only if it doesn't exist
            if 'title_text' not in existing_indexes:
                logger.info("Creating text index on 'title' field")
                await self.posts.create_index(
                    [("title", TEXT)],
                    background=True  # Non-blocking index creation
                )
            
            # Ensure channels collection exists with proper structure
            if "channels" not in await self.db.list_collection_names():
                await self.db.create_collection("channels")
                logger.info("Created channels collection")
                
                # Create recommended index for channel lookups
                await self.channels.create_index(
                    [("_id", 1)],
                    unique=True
                )

        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    async def update_channel_hash(self, channel_id: int, access_hash: int) -> None:
        """Atomic update of channel access hash"""
        try:
            result = await self.channels.update_one(
                {'_id': channel_id},
                {'$set': {'access_hash': access_hash}},
                upsert=True
            )
            logger.debug(f"Channel hash update result: {result.raw_result}")
        except Exception as e:
            logger.error(f"Failed to update channel hash: {str(e)}")
            raise

    async def get_channel_peer(self, bot: Any) -> raw.types.InputPeerChannel:
        """Get channel peer with fallback to cached data"""
        try:
            # First try fresh data from Telegram
            chat = await bot.app.get_chat(Config.SOURCE_CHANNEL_ID)
            await self.update_channel_hash(chat.id, chat.access_hash)
            
            return raw.types.InputPeerChannel(
                channel_id=chat.id,
                access_hash=chat.access_hash
            )
        except Exception as fresh_error:
            logger.warning(f"Fresh channel fetch failed: {str(fresh_error)}")
            
            # Fallback to cached data
            try:
                doc = await self.channels.find_one(
                    {'_id': Config.SOURCE_CHANNEL_ID},
                    {'access_hash': 1}
                )
                
                if doc and 'access_hash' in doc:
                    return raw.types.InputPeerChannel(
                        channel_id=doc['_id'],
                        access_hash=doc['access_hash']
                    )
                raise ValueError("No channel data available in cache")
            except Exception as cache_error:
                logger.error(f"Cache fallback failed: {str(cache_error)}")
                raise ConnectionError("Could not retrieve channel information")

    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Robust text search with error handling"""
        try:
            cursor = self.posts.find(
                {"$text": {"$search": query}},
                {
                    "score": {"$meta": "textScore"},
                    "title": 1,
                    "text": 1,
                    "message_id": 1,
                    "chat_id": 1
                }
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Search failed for '{query}': {str(e)}")
            return []

    async def close(self) -> None:
        """Graceful connection closure"""
        try:
            await self.client.close()
            logger.info("MongoDB connection closed cleanly")
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")
            raise
