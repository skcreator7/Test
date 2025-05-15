from pyrogram import Client, filters, types
from datetime import datetime
from config import Config
from database import Database

class TelegramBot:
    def __init__(self, db: Database):
        self.db = db
        self.app = Client(
            "telegram_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start(client, message: types.Message):
            await message.reply("🔍 This bot collects posts from a private channel")
        
        @self.app.on_message(filters.text & filters.private)
        async def search_handler(client, message: types.Message):
            query = message.text.strip()
            if not query:
                return await message.reply("Please enter a valid search query")
            
            results = await self.db.search_posts(query)
            if not results:
                return await message.reply("No results found in the private channel")
            
            first_result = results[0]
            web_url = f"{Config.BASE_URL}/watch/{str(first_result['_id'])}"
            
            reply_text = f"🔍 Found in private channel\n\n"
            reply_text += f"📄 {first_result.get('text', '')[:200]}...\n\n"
            reply_text += f"🌐 View on web: {web_url}"
            
            if len(results) > 1:
                reply_text += f"\n\n+ {len(results)-1} more results..."
            
            await message.reply(reply_text, disable_web_page_preview=True)
        
        @self.app.on_message(filters.channel)
        async def channel_handler(client, message: types.Message):
            """Only process messages from our source channel"""
            if message.chat.id == Config.SOURCE_CHANNEL_ID and message.text:
                await self.db.save_post(message)
