from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, DESCENDING, ASCENDING
import logging
from typing import List, Dict
from datetime import datetime, timedelta
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
            await self.posts.create_index(
                [("title", TEXT), ("description", TEXT)],
                name="text_title_description"
            )
            await self.posts.create_index([("channel_id", ASCENDING), ("message_id", ASCENDING)], unique=True)
            await self.channels.create_index([("channel_id", ASCENDING)], unique=True)
            logger.info("Database indexes created")
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            raise

    async def get_channels_to_scrape(self):
        return await self.channels.find({
            '$or': [
                {'last_scraped': {'$exists': False}},
                {'last_scraped': {'$lt': datetime.utcnow() - timedelta(hours=1)}}
            ],
            'scrape_status': {'$ne': 'disabled'}
        }).to_list(None)

    async def upsert_post(self, channel_id: int, message_id: int, data: dict):
        data['channel_id'] = channel_id
        data['message_id'] = message_id
        await self.posts.update_one(
            {'channel_id': channel_id, 'message_id': message_id},
            {'$set': data},
            upsert=True
        )

    async def update_channel_scrape_status(self, channel_id: int, last_scraped: datetime,
                                           status: str, new_posts: int = 0, error: str = None):
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
        await self.channels.update_one(
            {'channel_id': channel_data['channel_id']},
            {'$setOnInsert': channel_data},
            upsert=True
        )

    async def get_channels(self):
        return await self.channels.find().sort('name', 1).to_list(None)

    async def search_posts(self, query: str, limit: int = 5) -> List[Dict]:
        search_filter = {
            '$text': {'$search': query},
            'channel_id': {'$in': Config.CHANNEL_IDS}  # <-- Only search in allowed channels
        }
        cursor = self.posts.find(
            search_filter,
            {'score': {'$meta': 'textScore'}, 'channel_id': 1, 'title': 1, 'description': 1, 'links': 1, 'date': 1, 'size': 1}
        ).sort([('score', {'$meta': 'textScore'}), ('date', DESCENDING)]).limit(limit)
        return await cursor.to_list(length=limit)

    async def close(self):
        self.client.close()
        logger.info("Database connection closed")
