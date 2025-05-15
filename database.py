from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from bson import ObjectId
from datetime import datetime

class Database:
    def __init__(self):
        self.client = None
        self.db = None

    async def init_db(self):
        """Initialize with SRV support"""
        try:
            self.client = AsyncIOMotorClient(
                Config.MONGO_URI,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                serverSelectionTimeoutMS=30000
            )
            self.db = self.client[Config.MONGO_DB]
            await self.client.admin.command('ping')
            print("✅ MongoDB connected successfully")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise

    async def save_post(self, post_data: dict):
        post_data.update({
            'source': 'SOURCE_CHANNEL',
            'saved_at': datetime.utcnow()
        })
        return await self.db.posts.insert_one(post_data)

    async def search_posts(self, query: str, limit: int = 5):
        cursor = self.db.posts.find({
            'source': 'SOURCE_CHANNEL',
            '$text': {'$search': query}
        }).limit(limit)
        return await cursor.to_list(length=limit)

    async def close(self):
        if self.client:
            self.client.close()
