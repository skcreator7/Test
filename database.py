from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, DESCENDING, ASCENDING
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bson import ObjectId

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str = "movie_bot"):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.posts = self.db.posts
        self.channels = self.db.channels
        logger.info(f"Connected to MongoDB: {db_name}")

    async def initialize(self):
        """Create indexes"""
        try:
            await self.posts.create_index([("title", TEXT)])
            await self.posts.create_index([("description", TEXT)])
            await self.posts.create_index([("channel_id", ASCENDING), ("message_id", ASCENDING)], unique=True)
            await self.channels.create_index([("channel_id", ASCENDING)], unique=True)
            logger.info("Database indexes created")
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            raise

    async def get_channels_to_scrape(self):
        """Get channels that need to be scraped"""
        return await self.channels.find({
            '$or': [
                {'last_scraped': {'$exists': False}},
                {'last_scraped': {'$lt': datetime.utcnow() - timedelta(hours=1)}}
            ],
            'scrape_status': {'$ne': 'disabled'}
        }).to_list(None)

    async def upsert_post(self, channel_id: int, message_id: int, data: dict):
        """Insert or update a post"""
        data['channel_id'] = channel_id
        data['message_id'] = message_id
        await self.posts.update_one(
            {'channel_id': channel_id, 'message_id': message_id},
            {'$set': data},
            upsert=True
        )

    async def update_channel_scrape_status(self, channel_id: int, last_scraped: datetime,
                                           status: str, new_posts: int = 0, error: str = None):
        """Update channel scrape status"""
        update_fields = {
            'last_scraped': last_scraped,
            'scrape_status': status
        }
        if error:
            update_fields['last_error'] = error

        update_query = {'$set': update_fields}
        if new_posts:
            update_query['$inc'] = {'post_count': new_posts}

        await self.channels.update_one(
            {'channel_id': channel_id},
            update_query
        )

    async def add_channel(self, channel_data: dict):
        """Add a new channel to monitor"""
        await self.channels.update_one(
            {'channel_id': channel_data['channel_id']},
            {'$setOnInsert': channel_data},
            upsert=True
        )

    async def get_channels(self):
        """Get all monitored channels"""
        return await self.channels.find().sort('name', 1).to_list(None)

    async def search_posts(self, query: str, limit: int = 5) -> List[Dict]:
        """Search posts with text matching"""
        cursor = self.posts.find(
            {'$text': {'$search': query}},
            {'score': {'$meta': 'textScore'}}
        ).sort([('score', {'$meta': 'textScore'}), ('date', DESCENDING)]).limit(limit)

        return await cursor.to_list(length=limit)

    async def close(self):
        """Close database connection"""
        self.client.close()
        logger.info("Database connection closed")
