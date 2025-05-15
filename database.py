import motor.motor_asyncio
from config import Config
from bson.objectid import ObjectId

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URL)
        self.db = self.client[Config.DB_NAME]

    async def init_db(self):
        await self.db.posts.create_index([("title", "text"), ("content", "text")])

    async def save_post(self, message):
        title = message.caption or message.text or "Untitled"
        links = []
        lines = title.splitlines()
        for line in lines:
            if "http" in line:
                if "|" in line:
                    q, u = line.split("|", 1)
                    links.append((q.strip(), u.strip()))
                else:
                    links.append(("Link", line.strip()))
        if links:
            await self.db.posts.insert_one({
                "message_id": message.message_id,
                "channel_id": message.chat.id,
                "title": title.splitlines()[0],
                "content": title,
                "links": links
            })

    async def search_posts(self, query):
        cursor = self.db.posts.find({"$text": {"$search": query}})
        return await cursor.to_list(length=30)

    async def get_post(self, post_id):
        return await self.db.posts.find_one({"_id": ObjectId(post_id)})
