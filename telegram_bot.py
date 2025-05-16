import re
from typing import List
from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo.collection import Collection


class TelegramBot:
    def __init__(self, client: Client, db):
        self.client = client
        self.db = db
        self.posts: Collection = db.posts

        # Monitor new posts in channels
        self.client.add_handler(
            handler=filters.channel,
            callback=self.save_post
        )

        # For search queries in private or group
        @self.client.on_message(filters.text & (filters.private | filters.group))
        async def search_handler(client, message: Message):
            query = message.text.strip()
            results = await self._search_posts(query)
            if not results:
                await message.reply("No results found.")
                return
            reply = "Search Results:\n\n"
            for item in results:
                reply += f"• {item['title']}\nhttps://your-domain/watch/{item['_id']}/{item['title'].replace(' ', '-')}\n\n"
            await message.reply(reply)

    async def save_post(self, client: Client, message: Message):
        if not message.text and not message.caption:
            return

        content = message.text or message.caption
        links = self.extract_links(content)
        if not links:
            return

        title = content.split('\n')[0].strip()
        post_data = {
            "chat_id": message.chat.id,
            "message_id": message.id,
            "title": title,
            "content": content,
            "links": links
        }

        await self.posts.update_one(
            {"chat_id": message.chat.id, "message_id": message.id},
            {"$set": post_data},
            upsert=True
        )

    def extract_links(self, text: str) -> List[dict]:
        lines = text.split('\n')
        links = []
        for line in lines:
            match = re.match(r"^\s*[\W\s]*([\w\s]+)\s*:\s*(https?://\S+)", line)
            if match:
                label = match.group(1).strip()
                url = match.group(2).strip()
                links.append({"label": label, "url": url})
        return links

    async def _search_posts(self, query: str) -> List[dict]:
        cursor = self.posts.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(10)

        results = []
        async for doc in cursor:
            results.append(doc)
        return results
