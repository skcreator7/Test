from pyrogram import Client, filters, types
from config import Config
from utils import extract_links, slugify_title


class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.app = Client(
            "my_telegram_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.setup_handlers()

    async def start(self):
        await self.app.start()
        print("Telegram Bot Started!")

    async def stop(self):
        await self.app.stop()

    def setup_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: types.Message):
            await message.reply("🔍 Send any search term to find streaming links.")

        @self.app.on_message(filters.text & filters.private)
        async def handle_search(client, message: types.Message):
            query = message.text.strip()
            if not query:
                await message.reply("❌ Please send a search keyword.")
                return

            results = await self.db.search_posts(query)
            if not results:
                await message.reply("❌ No results found.")
                return

            response = "🎬 *Search Results:*\n\n"
            for post in results[:10]:
                title = post.get("title", "Untitled")
                slug = slugify_title(title)
                response += f"• [{title}](https://{Config.BASE_DOMAIN}/watch/{post['_id']}/{slug})\n"

            await message.reply(response, disable_web_page_preview=True)

        @self.app.on_message(filters.channel)
        async def save_channel_post(client, message: types.Message):
            links = extract_links(message.text or "")
            if links:
                await self.db.save_post(message)
