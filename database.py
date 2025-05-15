from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
import re

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client[Config.MONGO_DB]
        self.posts = self.db.posts
    
    async def init_db(self):
        await self.posts.create_index("message_id")
        await self.posts.create_index([("text", "text")])
    
    async def save_post(self, message):
        """Save post from our source channel only"""
        if message.chat.id != Config.SOURCE_CHANNEL_ID:
            return None
            
        post = {
            "message_id": message.id,
            "chat_id": Config.SOURCE_CHANNEL_ID,
            "chat_title": message.chat.title,
            "text": message.text,
            "date": message.date,
            "links": self.extract_links(message.text),
            "last_accessed": datetime.now()
        }
        await self.posts.update_one(
            {"message_id": message.id},
            {"$set": post},
            upsert=True
        )
        return post
    
    def extract_links(self, text: str):
        if not text:
            return []
            
        links = []
        url_pattern = re.compile(r'https?://[^\s]+')
        
        for url in url_pattern.findall(text):
            quality = self.detect_quality(url)
            links.append({
                "url": url,
                "quality": quality,
                "label": f"Download {quality}" if quality else "Download"
            })
        return links
    
    def detect_quality(self, text: str):
        for quality, pattern in Config.QUALITY_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return quality
        return None
    
    async def search_posts(self, query: str, limit: int = 10):
        """Search only within our source channel posts"""
        return await self.posts.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit).to_list(None)
    
    async def get_post(self, post_id: str):
        if not ObjectId.is_valid(post_id):
            return None
        return await self.posts.find_one({"_id": ObjectId(post_id)})
