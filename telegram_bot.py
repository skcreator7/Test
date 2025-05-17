from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from config import Config

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.client = TelegramClient(
            StringSession(Config.STRING_SESSION),
            Config.API_ID,
            Config.API_HASH
        )

    async def start(self):
        await self.client.start()
        self.add_handlers()

    async def stop(self):
        await self.client.disconnect()

    def add_handlers(self):
        # Channel me nayi post aaye to DB me save ho
        @self.client.on(events.NewMessage(chats=Config.SOURCE_CHANNEL_ID))
        async def auto_save_new_post(event):
            msg = event.message
            doc = {
                "_id": msg.id,
                "text": msg.text or "",
                "title": (msg.text or "").split("\n")[0][:64] if msg.text else "",
                "date": msg.date,
                "from_channel": Config.SOURCE_CHANNEL_ID
            }
            await self.db.save_post(doc)

        # Channel se post delete ho to DB se bhi delete ho
        @self.client.on(events.MessageDeleted(chats=Config.SOURCE_CHANNEL_ID))
        async def auto_delete_post(event):
            for msg_id in event.deleted_ids:
                await self.db.delete_post(msg_id)

        # /start command
        @self.client.on(events.NewMessage(pattern=r'^/start'))
        async def start_handler(event):
            await event.respond(
                "👋 <b>Welcome to Movie Search Bot!</b>\n\n"
                "Just type the name of any movie or series to search instantly.\n"
                "You can also use the web version: [Open Web App]({})".format(Config.BASE_URL),
                parse_mode='html',
                buttons=[
                    [Button.url("🌐 Open Web App", Config.BASE_URL)]
                ]
            )

        # Search: bina command ke bhi
        @self.client.on(events.NewMessage())
        async def instant_search_handler(event):
            text = event.raw_text.strip()
            if text.startswith('/'):
                return
            if not text:
                return
            reply = await event.respond(f"⏳ Searching for <b>{text}</b>...", parse_mode='html')
            results = await self.db.search_posts(text)
            if results:
                resp_text = f"🔎 <b>Search Results for:</b> <code>{text}</code>\n"
                buttons = []
                for post in results:
                    title = post['title']
                    post_id = post['_id']
                    url = f"{Config.BASE_URL}/view/{post_id}?q={text}"
                    buttons.append([Button.url(title, url)])
                    resp_text += f"• <b>{title}</b>\n"
                await reply.edit(resp_text, buttons=buttons, parse_mode='html')
            else:
                await reply.edit(f"❌ No results found for <b>{text}</b>.", parse_mode='html')
