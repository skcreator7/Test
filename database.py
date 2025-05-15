from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from bson import ObjectId
from datetime import datetime

class Database:
    def __init__(self):
        self.client = None
        self.db = None

    async def init_db(self):
        """Initialize database connection and create indexes"""
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client[Config.MONGO_DB]
        
        # Create text index for searching
        await self.db.posts.create_index([("text", "text")])
        
        # Verify connection
        await self.client.admin.command('ping')
        print("✅ MongoDB connected with text index")

    async def save_post(self, post_data: dict):
        """Save post to database with metadata"""
        post_data.update({
            "source": "SOURCE_CHANNEL",
            "saved_at": datetime.utcnow()
        })
        result = await self.db.posts.insert_one(post_data)
        return result.inserted_id

    async def search_posts(self, query: str, limit: int = 5):
        """Search posts using MongoDB text search"""
        return await self.db.posts.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit).to_list(None)

    async def get_post_count(self):
        """Get count of all posts"""
        return await self.db.posts.count_documents({})

    async def close(self):
        """Cleanly close connection"""
        if self.client:
            self.client.close()
