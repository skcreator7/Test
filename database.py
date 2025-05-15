from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import asyncio

class Database:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """Initialize connection with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.client = AsyncIOMotorClient(
                    Config.MONGO_URI,
                    connectTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000
                )
                self.db = self.client[Config.MONGO_DB]
                await self.client.admin.command('ping')
                print("✅ MongoDB connected successfully")
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = (attempt + 1) * 2
                print(f"⚠️ Connection failed (attempt {attempt + 1}), retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

    async def close(self):
        if self.client:
            self.client.close()
