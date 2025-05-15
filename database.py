from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from bson import ObjectId
from datetime import datetime

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client[Config.MONGO_DB]
    
    async def save_post(self, post_data: dict):
        """Save post with source channel marker"""
        post_data.update({
            "source": "SOURCE_CHANNEL",
            "saved_at": datetime.utcnow()
        })
        result = await self.db.posts.insert_one(post_data)
        return result.inserted_id
    
    async def search_posts(self, query: str, limit: int = 5):
        """Search only source channel posts"""
        return await self.db.posts.find(
            {
                "source": "SOURCE_CHANNEL",
                "$text": {"$search": query}
            },
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit).to_list(None)
    
    async def get_post_count(self):
        """Count only source channel posts"""
        return await self.db.posts.count_documents({"source": "SOURCE_CHANNEL"})
    
    async def ping(self):
        """Check database connection"""
        await self.db.command("ping")
