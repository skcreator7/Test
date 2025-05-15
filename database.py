from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import asyncio

class Database:
    def __init__(self):
        self.client = None
        self.db = None

    async def init_db(self, max_retries=3, retry_delay=5):
        for attempt in range(max_retries):
            try:
                self.client = AsyncIOMotorClient(Config.MONGO_URI)
                self.db = self.client[Config.MONGO_DB]
                await self.ping()  # Test connection
                print("DB connected!")
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"DB connection failed (attempt {attempt+1}), retrying...")
                await asyncio.sleep(retry_delay)

    async def ping(self):
        await self.db.command("ping")

    async def save_post(self, post_data):
        await self.db.posts.insert_one(post_data)

    async def search_posts(self, query, limit=10):
        return await self.db.posts.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit).to_list()
