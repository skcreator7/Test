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
            "chat_id": Config.SOURCE_CHANNEL_ID,
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
        """Improved link extraction with quality detection"""
        if not text:
            return []
            
        links = []
        url_pattern = re.compile(
            r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .@?^=%&:/~+#-]*'
        )
        
        for url in re.findall(url_pattern, text):
            clean_url = url.rstrip('.,;!?')
            
            if any(skip in clean_url.lower() for skip in ['t.me', 'telegram.me']):
                continue
                
            quality = self.detect_quality(clean_url)
            label = f"Download {quality}" if quality else "Open Link"
            
            links.append({
                "url": clean_url,
                "quality": quality or "unknown",
                "label": label
            })
        return links
    
    def detect_quality(self, text: str):
        """Detect video quality from text"""
        match = re.search(
            r'(\d{3,4}p)\s*(HEVC|HDRip)?', 
            text, 
            re.IGNORECASE
        )
        return match.group(1).lower() if match else None
    
    async def search_posts(self, query: str, limit: int = 10):
        """Search posts with text index"""
        return await self.posts.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit).to_list(None)
    
    async def get_post(self, post_id: str):
        if not ObjectId.is_valid(post_id):
            return None
        return await self.posts.find_one({"_id": ObjectId(post_id)})
