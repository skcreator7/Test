from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
import re

class Database:
    def __init__(self, uri=None):
        from config import Config
        self.client = AsyncIOMotorClient(uri or Config.MONGO_URI)
        self.db = self.client["telegram_stream_db"]
        self.posts = self.db["posts"]
        self.channels = self.db["channels"]

    async def init_db(self):
        await self.posts.create_index([("text", "text")])
        await self.channels.create_index("chat_id", unique=True)

    async def save_post(self, message):
        if not message.text:
            return

        links = re.findall(r'(https?://[^\s]+)', message.text)
        if not links:
            return

        post_data = {
            "message_id": message.id,
            "chat_id": message.chat.id,
            "text": message.text,
            "links": links,
            "date": message.date,
            "channel_name": message.chat.title or message.chat.first_name or "Unknown"
        }
        await self.posts.update_one(
            {"chat_id": message.chat.id, "message_id": message.id},
            {"$set": post_data},
            upsert=True
        )

    async def search_posts(self, query):
        cursor = self.posts.find({"$text": {"$search": query}}).sort("date", -1).limit(10)
        return await cursor.to_list(length=10)

    async def get_post_by_id(self, post_id):
        return await self.posts.find_one({"_id": ObjectId(post_id)})
