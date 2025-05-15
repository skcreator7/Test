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
        """Save post from source channel"""
        if message.chat.id != Config.SOURCE_CHANNEL_ID:
            return None
        
        post = {
            "message_id": message.id,
            "chat_id": message.chat.id,
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
        """Extracts all valid links and assigns quality labels if possible."""
        if not text:
            return []

        links = []
        url_pattern = re.compile(
            r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .@?^=%&:/~+#-]*'
        )
        matches = re.findall(url_pattern, text)

        for url in matches:
            url = url.strip().rstrip('.,;!?')
            if "t.me" in url or "telegram.me" in url:
                continue
            
            quality = self.detect_quality(url)
            label = quality.upper() if quality else "Open Link"
            
            links.append({
                "url": url,
                "quality": quality or "unknown",
                "label": label
            })
        return links

    def detect_quality(self, text: str):
        """Detects common video quality labels like 480p, 720p, 1080p, etc."""
        match = re.search(r'(\d{3,4}p)', text, re.IGNORECASE)
        return match.group(1).lower() if match else None

    async def search_posts(self, query: str, limit: int = 10):
        """Search posts by text"""
        return await self.posts.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit).to_list(None)

    async def get_post(self, post_id: str):
        """Fetch post by ObjectId"""
        if not ObjectId.is_valid(post_id):
            return None
        return await self.posts.find_one({"_id": ObjectId(post_id)})
