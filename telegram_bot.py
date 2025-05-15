from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database import Database
import asyncio

class TelegramBot:
    def __init__(self, db: Database):
        self.db = db
        self.app = Client(
            "my_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.setup_handlers()

    async def start(self):
        await self.app.start()
        print(f"🤖 Bot started monitoring channel: {Config.SOURCE_CHANNEL_ID}")

    async def stop(self):
        await self.app.stop()

    async def auto_delete(self, message: Message, delay: int):
        """Auto-deletes message after delay, skips source channel"""
        if message.chat.id == Config.SOURCE_CHANNEL_ID:
            return
            
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except Exception as e:
            print(f"⚠️ Couldn't delete message: {e}")

    def setup_handlers(self):
        # Save only from source channel (no auto-delete)
        @self.app.on_message(filters.channel & filters.chat(Config.SOURCE_CHANNEL_ID))
        async def save_channel_post(_, message: Message):
            post_data = {
                'channel_id': message.chat.id,
                'message_id': message.id,
                'text': message.text or message.caption,
                'date': message.date,
                'source': 'SOURCE_CHANNEL'
            }
            await self.db.save_post(post_data)
            print(f"💾 Saved post #{message.id}")

        # Search handler (auto-deletes)
        @self.app.on_message(filters.text & ~filters.command)
        async def handle_search(_, message: Message):
            query = message.text.strip()
            results = await self.db.search_posts(query)
            
            if not results:
                reply = await message.reply("🔍 No matching posts found")
                asyncio.create_task(self.auto_delete(reply, Config.AUTO_DELETE['not_found']))
                return
                
            buttons = [
                [InlineKeyboardButton(
                    f"📌 {res.get('title', 'Post')}",
                    url=f"{Config.BASE_URL}/watch/{res['_id']}"
                )]
                for res in results[:5]
            ]
            
            reply = await message.reply(
                f"🔎 Found {len(results)} posts:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            asyncio.create_task(self.auto_delete(reply, Config.AUTO_DELETE['search_results']))

        # Start command (auto-deletes)
        @self.app.on_message(filters.command("start"))
        async def start_command(_, message: Message):
            reply = await message.reply("Send text to search posts")
            asyncio.create_task(self.auto_delete(reply, Config.AUTO_DELETE['help_messages']))

        # Admin commands (no auto-delete)
        if hasattr(Config, 'ADMINS') and Config.ADMINS:
            @self.app.on_message(filters.command("stats") & filters.user(Config.ADMINS))
            async def stats_command(_, message: Message):
                count = await self.db.get_post_count()
                await message.reply(f"📊 Posts in DB: {count}")
