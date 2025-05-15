from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from bson import ObjectId
from datetime import datetime

class Database:
    def __init__(self):
        self.client = None
        self.db = None

    async def init_db(self):
        """Initialize connection with retry logic"""
        try:
            self.client = AsyncIOMotorClient(Config.MONGO_URI)
            self.db = self.client[Config.MONGO_DB]
            await self.client.admin.command('ping')
            print("✅ MongoDB connection established")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise

    async def save_post(self, post_data: dict):
        """Save post with source channel marker"""
        post_data.update({
            'source': 'SOURCE_CHANNEL',
            'saved_at': datetime.utcnow()
        })
        result = await self.db.posts.insert_one(post_data)
        return result.inserted_id

    async def search_posts(self, query: str, limit: int = 5):
        """Search with backward-compatible method"""
        cursor = self.db.posts.find(
            {
                'source': 'SOURCE_CHANNEL',
                '$text': {'$search': query}
            }
        ).limit(limit)
        
        return await cursor.to_list(length=limit)

    async def get_post_count(self):
        """Count documents with backward-compatible method"""
        return await self.db.posts.count_documents({'source': 'SOURCE_CHANNEL'})

    async def close(self):
        """Properly close connection"""
        if self.client:
            self.client.close()
