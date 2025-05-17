import asyncio
from telethon import TelegramClient, events, Button
import logging
from config import Config

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.client = TelegramClient(
            "bot",
            Config.API_ID,
            Config.API_HASH
        ).start(bot_token=Config.BOT_TOKEN)
        self.last_messages = {}  # user_id: [list of message ids]

    async def start(self):
        logging.info("Starting Telegram bot...")
        self.client.add_event_handler(self.start_cmd, events.NewMessage(pattern="/start"))
        self.client.add_event_handler(self.search_query, events.NewMessage(func=lambda e: not e.text.startswith("/")))
        await self.client.start()
        logging.info("Telegram bot started.")

    async def stop(self):
        await self.client.disconnect()

    async def start_cmd(self, event):
        await event.respond(
            "👋 *Welcome!*\n\nSend me any movie or series name to search.",
            parse_mode="md"
        )

    async def search_query(self, event):
        query = event.text.strip()
        user_id = event.sender_id

        if len(query) < 2:
            m = await event.respond("❌ Please enter at least 2 characters.")
            await asyncio.sleep(10)
            await m.delete()
            return

        results = await self.db.search_posts(query, limit=6)
        # Clean up previous bot messages for this user for spam-free UX
        if user_id in self.last_messages:
            for msg_id in self.last_messages[user_id]:
                try:
                    await self.client.delete_messages(event.chat_id, msg_id)
                except Exception:
                    pass
            self.last_messages[user_id] = []

        if not results:
            m = await event.respond("❌ No results found.")
            await asyncio.sleep(10)
            await m.delete()
            return

        msg_ids = []
        for post in results:
            url = f"{Config.BASE_URL}/post/{post['_id']}"
            btn = [Button.url("🔗 View Post", url)]
            msg = await event.respond(
                f"**{post['title']}**",
                buttons=btn,
                parse_mode="md"
            )
            msg_ids.append(msg.id)
            await asyncio.sleep(1)

        # Try to delete user's query after showing result
        try:
            await event.delete()
        except Exception:
            pass

        # Schedule deleting results after 30 seconds
        async def auto_delete(ids):
            await asyncio.sleep(30)
            for mid in ids:
                try:
                    await self.client.delete_messages(event.chat_id, mid)
                except Exception:
                    pass

        asyncio.create_task(auto_delete(msg_ids))
        self.last_messages[user_id] = msg_ids
