from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
from pyrogram.types import InputPeerChannel
import logging
from typing import Dict
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = "movie_bot"):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.posts = self.db.posts
        self.channels = self.db.channels
        logger.info(f"Connected to MongoDB: {db_name}")

    async def initialize(self):
        try:
            current_indexes = await self.posts.index_information()
            
            text_index_exists = any(
                any('text' in str(field) for field in index.get('key', []))
                for index in current_indexes.values()
            )
            
            if not text_index_exists:
                await self.posts.create_index([("title", TEXT)])
                await self.posts.create_index([("text", TEXT)])
                logger.info("Search indexes created successfully")
            
            # Ensure channel collection has index
            await self.channels.create_index([("_id", 1)], unique=True)
        except Exception as e:
            logger.error(f"Index creation failed: {e}")

    async def update_channel_hash(self, channel_id: int, access_hash: int):
        await self.channels.update_one(
            {'_id': channel_id},
            {'$set': {'access_hash': access_hash}},
            upsert=True
        )

    async def get_channel_peer(self, bot):
        try:
            chat = await bot.app.get_chat(Config.SOURCE_CHANNEL_ID)
            await self.update_channel_hash(chat.id, chat.access_hash)
            return InputPeerChannel(chat.id, chat.access_hash)
        except Exception as e:
            logger.error(f"Failed to get channel peer: {e}")
            doc = await self.channels.find_one({'_id': Config.SOURCE_CHANNEL_ID})
            if doc and doc.get('access_hash'):
                return InputPeerChannel(doc['_id'], doc['access_hash'])
            raise

    async def search_posts(self, query: str, limit: int = 10) -> List[Dict]:
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
        await self.client.close()
