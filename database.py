from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from config import Config
import re

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client[Config.MONGO_DB]
        self.posts = self.db.posts

    async def init_db(self):
        await self.posts.create_index([("text", "text")])
    
    async def ping(self):
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB Error: {e}")
            return False
    
    async def save_post(self, message):
        # ... (पिछला कोड यहाँ ऐड करें) ...

    async def search_posts(self, query):
        # ... (पिछला कोड यहाँ ऐड करें) ...
    
    async def close(self):
        self.client.close()
