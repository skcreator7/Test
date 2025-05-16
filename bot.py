import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from bson import ObjectId

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, client: Client, db):
        self.client = client
        self.db = db

        self.client.add_handler(filters.chat_type.groups | filters.chat_type.private, self.search_handler, group=1)
        self.client.add_handler(filters.channel, self.channel_post_handler, group=2)

    async def search_handler(self, client: Client, message: Message):
        if not message.text:
            return

        query = message.text.strip()

        if len(query) < 3:
            await message.reply("Please enter a longer search query.")
            return

        results = self.db.posts.find({"$text": {"$search": query}}).sort(
            [("score", {"$meta": "textScore"})]
        ).limit(5)

        reply = f"**Search Results for:** `{query}`\n\n"
        found = False

        async for doc in results:
            found = True
            post_id = str(doc["_id"])
            title = doc.get("title", "Untitled")
            title_slug = title.replace(" ", "-")
            url = f"{os.getenv('BASE_URL')}/watch/{post_id}/{title_slug}"
            reply += f"• [{title}]({url})\n"

        if not found:
            reply = "No matching posts found."

        await message.reply(reply, disable_web_page_preview=True)

    async def channel_post_handler(self, client: Client, message: Message):
        if not message.text:
            return

        text = message.text
        title_line = text.splitlines()[0]
        title = title_line.strip()

        links = []
        for line in text.splitlines():
            match = re.search(r"(https?://\S+)", line)
            if match:
                label = line.split(":")[0].strip(" 🎞️") if ":" in line else "Link"
                links.append({
                    "label": label,
                    "url": match.group(1)
                })

        if not links:
            return  # Skip posts without links

        # Save to DB
        await self.db.posts.update_one(
            {"message_id": message.id, "chat_id": message.chat.id},
            {"$set": {
                "title": title,
                "text": text,
                "links": links,
                "chat_id": message.chat.id,
                "message_id": message.id
            }},
            upsert=True
        )

        logger.info(f"Saved post: {title}")
