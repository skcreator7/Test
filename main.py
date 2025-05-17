import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import Config
from database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scrape_new_posts_only(db):
    # 1. Find the latest message _id in DB
    last = await db.posts.find_one(sort=[("_id", -1)])  # Descending order
    last_id = last["_id"] if last else 0

    logger.info(f"Last post ID in DB: {last_id}")

    async with TelegramClient(StringSession(Config.STRING_SESSION), Config.API_ID, Config.API_HASH) as client:
        # 2. Fetch only new messages (greater than last_id)
        async for message in client.iter_messages(
            Config.SOURCE_CHANNEL_ID,
            min_id=last_id,
            reverse=True
        ):
            if not message.text and not message.message:
                continue
            post = {
                "_id": message.id,
                "title": (message.text or message.message or "").split('\n')[0][:120],
                "text": (message.text or message.message or ""),
                "date": message.date,
                "from_id": getattr(message.from_id, 'user_id', None)
            }
            # 3. Upsert: Insert if not exists, update if already present
            await db.posts.update_one({"_id": post["_id"]}, {"$set": post}, upsert=True)
            logger.info(f"Saved post: {post['_id']} - {post['title'][:40]}")
    logger.info("Scraping completed: only new posts.")

# Example usage in your flow:
# asyncio.run(scrape_new_posts_only(db))
