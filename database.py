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
        try:
            post_data = {
                "_id": message.id,
                "chat_id": message.chat.id,
                "text": message.text,
                "links": self.extract_links(message.text),
            }
            result = await self.posts.replace_one(
                {"_id": message.id}, 
                post_data, 
                upsert=True
            )
            return result.upserted_id
        except Exception as e:
            print(f"Error saving post: {e}")
            raise
    
    async def search_posts(self, query):
        try:
            cursor = self.posts.find({"$text": {"$search": query}})
            return await cursor.to_list(length=20)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def extract_links(self, text):
        pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .\-?=%&]*'
        return re.findall(pattern, text)
    
    async def close(self):
        self.client.close()
