from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from config import Config

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client[Config.MONGO_DB]
        self.posts = self.db.posts

    async def init_db(self):
        await self.posts.create_index([("text", "text")])

    async def save_post(self, message):
        post_data = {
            "_id": message.id,
            "chat_id": message.chat.id,
            "text": message.text,
            "links": self.extract_links(message.text),
        }
        await self.posts.replace_one({"_id": message.id}, post_data, upsert=True)

    async def search_posts(self, query):
        cursor = self.posts.find({"$text": {"$search": query}})
        return await cursor.to_list(length=20)

    def extract_links(self, text):
        import re
        return re.findall(r'https?://[^\s]+', text)
