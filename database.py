from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
from pyrogram import raw
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = "movie_bot") -> None:
        self.client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=30000,
            connectTimeoutMS=10000,
            retryWrites=True,
            replicaSet='atlas-yg410i-shard-0'
        )
        self.db = self.client[db_name]
        self.posts = self.db.posts
        self.channels = self.db.channels

    async def initialize(self) -> None:
        """Initialize database with proper text index handling"""
        try:
            # Get existing indexes
            existing_indexes = await self.posts.index_information()
            
            # Check if we already have a text index
            text_index_exists = any(
                idx.get('key', {}).get('_fts') == 'text' 
                for idx in existing_indexes.values()
            )
            
            if text_index_exists:
                logger.info("Text index already exists, skipping creation")
            else:
                # Create a combined text index if none exists
                await self.posts.create_index(
                    [("text", TEXT), ("title", TEXT)],
                    name="search_text",
                    background=True
                )
                logger.info("Created combined text index on 'text' and 'title' fields")

            # Ensure channels collection exists
            if "channels" not in await self.db.list_collection_names():
                await self.db.create_collection("channels")
                await self.channels.create_index([("_id", 1)])
                logger.info("Created channels collection")

        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    async def search_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search using the existing text index"""
        try:
            cursor = self.posts.find(
                {"$text": {"$search": query}},
                {
                    "score": {"$meta": "textScore"},
                    "title": 1,
                    "text": 1,
                    "msg_id": 1
                }
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    async def update_channel_hash(self, channel_id: int, access_hash: int) -> None:
        """Update channel access hash"""
        await self.channels.update_one(
            {'_id': channel_id},
            {'$set': {'access_hash': access_hash}},
            upsert=True
        )

    async def get_channel_peer(self, bot: Any) -> raw.types.InputPeerChannel:
        """Get channel peer with fallback to cached data"""
        try:
            chat = await bot.app.get_chat(Config.SOURCE_CHANNEL_ID)
            await self.update_channel_hash(chat.id, chat.access_hash)
            return raw.types.InputPeerChannel(
                channel_id=chat.id,
                access_hash=chat.access_hash
            )
        except Exception as e:
            logger.warning(f"Failed to get fresh channel info: {str(e)}")
            doc = await self.channels.find_one({'_id': Config.SOURCE_CHANNEL_ID})
            if doc:
                return raw.types.InputPeerChannel(
                    channel_id=doc['_id'],
                    access_hash=doc['access_hash']
                )
            raise ConnectionError("Could not retrieve channel information")

    async def close(self) -> None:
        """Close connection cleanly"""
        await self.client.close()
