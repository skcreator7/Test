from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config, WarningLevel
import re

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client[Config.MONGO_DB]
        self.posts = self.db.posts
        self.channels = self.db.channels
        self.users = self.db.users
        self.warnings = self.db.warnings
        self.message_logs = self.db.message_logs
    
    async def init_db(self):
        await self.posts.create_index("message_id")
        await self.posts.create_index("chat_id")
        await self.posts.create_index([("text", "text")])
        await self.channels.create_index("channel_id", unique=True)
        await self.message_logs.create_index([("chat_id", 1), ("user_id", 1)])
        await self.message_logs.create_index([("timestamp", -1)])
        await self.warnings.create_index([("expires_at", 1)], expireAfterSeconds=0)
    
    async def save_post(self, message):
        post = {
            "message_id": message.id,
            "chat_id": message.chat.id,
            "chat_title": message.chat.title,
            "text": message.text,
            "date": message.date,
            "links": self.extract_links(message.text),
            "last_accessed": datetime.now()
        }
        await self.posts.update_one(
            {"message_id": message.id, "chat_id": message.chat.id},
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
        return await self.posts.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit).to_list(None)
    
    async def get_post(self, post_id: str):
        if not ObjectId.is_valid(post_id):
            return None
        return await self.posts.find_one({"_id": ObjectId(post_id)})
    
    async def add_warning(self, chat_id: int, user_id: int, reason: str, level: WarningLevel = WarningLevel.WARNING):
        await self.warnings.insert_one({
            "chat_id": chat_id,
            "user_id": user_id,
            "reason": reason,
            "level": level.value,
            "timestamp": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=Config.WARNING_EXPIRE_HOURS)
        })
    
    async def get_warning_count(self, chat_id: int, user_id: int):
        warnings = await self.warnings.find({
            "chat_id": chat_id,
            "user_id": user_id,
            "expires_at": {"$gt": datetime.now()}
        }).to_list(None)
        return len(warnings), warnings
    
    async def clear_warnings(self, chat_id: int, user_id: int):
        await self.warnings.delete_many({
            "chat_id": chat_id,
            "user_id": user_id
        })
