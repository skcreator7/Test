import re
from pyrogram import Client, filters
from pyrogram.types import Message
from bson import ObjectId
from datetime import datetime

LINK_REGEX = r'(https?://[^\s]+)'
CHANNEL_USERNAMES = ["channelusername1", "channelusername2"]  # Replace with your channel usernames

class TelegramBot:
    def __init__(self, client: Client, db):
        self.client = client
        self.db = db

        @client.on_message(filters.text & filters.private)
        async def handle_private_message(bot, message: Message):
            await self.process_query(message)

        @client.on_message(filters.text & filters.group)
        async def handle_group_message(bot, message: Message):
            await self.process_query(message)

    async def process_query(self, message: Message):
        query = message.text.strip()
        if len(query) < 3:
            await message.reply("Please enter a longer search query.")
            return

        posts_collection = self.db["posts"]
        results = posts_collection.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(1)

        result = await results.to_list(length=1)
        if not result:
            await message.reply("No matching posts found.")
            return

        post = result[0]
        post_id = str(post["_id"])
        title = post.get("title", "Untitled").replace(" ", "-")[:40]
        watch_url = f"https://your-app-name.koyeb.app/watch/{post_id}/{title}"

        await message.reply(f"Here you go:\n{watch_url}")

    async def save_post(self, message: Message):
        if not message.text:
            return

        links = re.findall(LINK_REGEX, message.text)
        if not links:
            return

        post_data = {
            "text": message.text,
            "links": links,
            "title": message.text.split("\n")[0][:100],
            "chat_id": message.chat.id,
            "message_id": message.id,
            "date": datetime.utcnow()
        }

        await self.db["posts"].update_one(
            {"chat_id": message.chat.id, "message_id": message.id},
            {"$setOnInsert": post_data},
            upsert=True
        )

    async def monitor_channels(self):
        for username in CHANNEL_USERNAMES:
            async for message in self.client.get_chat_history(username, limit=100):
                await self.save_post(message)
