from pyrogram import Client, filters, types
from pyrogram.enums import ChatMemberStatus, ChatType
from datetime import datetime
import asyncio
from config import Config, WarningLevel
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
            await self.db.users.update_one(
                {"user_id": message.from_user.id},
                {"$set": {
                    "username": message.from_user.username,
                    "first_name": message.from_user.first_name,
                    "last_name": message.from_user.last_name,
                    "last_active": datetime.now()
                }},
                upsert=True
            )
            await message.reply("🔍 Send me a query to search across channels!")
        
        @self.app.on_message(filters.text & filters.private)
        async def search_handler(client, message: types.Message):
            query = message.text.strip()
            if not query:
                return await message.reply("Please enter a valid search query")
            
            await self.db.users.update_one(
                {"user_id": message.from_user.id},
                {"$push": {"search_history": {
                    "query": query,
                    "date": datetime.now()
                }}}
            )
            
            results = await self.db.search_posts(query)
            if not results:
                return await message.reply("No results found")
            
            first_result = results[0]
            web_url = f"{Config.BASE_URL}/watch/{str(first_result['_id'])}"
            
            reply_text = f"🔍 Found in {first_result.get('chat_title', 'Unknown Channel')}\n\n"
            reply_text += f"📄 {first_result.get('text', '')[:200]}...\n\n"
            reply_text += f"🌐 View on web: {web_url}"
            
            if len(results) > 1:
                reply_text += f"\n\n+ {len(results)-1} more results..."
            
            await message.reply(reply_text, disable_web_page_preview=True)
        
        @self.app.on_message(filters.channel)
        async def channel_handler(client, message: types.Message):
            if message.text:
                await self.db.save_post(message)
        
        @self.app.on_message(filters.group)
        async def group_message_handler(client, message: types.Message):
            try:
                if await self.is_admin(message.chat.id, message.from_user.id):
                    return
                    
                if await self.handle_restricted_content(message):
                    return
                    
                if Config.DELETE_USER_MESSAGES:
                    await message.delete()
                    
            except Exception as e:
                print(f"Error handling group message: {e}")
        
        @self.app.on_message(filters.bot & filters.group)
        async def bot_message_handler(client, message: types.Message):
            if Config.DELETE_BOT_REPLIES_AFTER > 0:
                await self.schedule_delete(message)
    
    async def is_admin(self, chat_id: int, user_id: int) -> bool:
        try:
            chat_member = await self.app.get_chat_member(chat_id, user_id)
            return chat_member.status in [
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR
            ]
        except:
            return False
    
    async def contains_restricted_content(self, message: types.Message) -> tuple:
        if not message.text:
            return False, ""
            
        text = message.text.lower()
        reasons = []
        
        if Config.DELETE_LINKS and ("http://" in text or "https://" in text):
            reasons.append("links")
            
        if Config.DELETE_USERNAMES and ("@" in text or "t.me/" in text):
            reasons.append("usernames")
            
        if reasons:
            return True, f"Message contains {' and '.join(reasons)}"
        return False, ""
    
    async def handle_restricted_content(self, message: types.Message) -> bool:
        has_restricted, reason = await self.contains_restricted_content(message)
        if not has_restricted:
            return False
            
        try:
            await message.delete()
        except:
            pass
            
        warning_count, _ = await self.db.get_warning_count(message.chat.id, message.from_user.id)
        await self.db.add_warning(
            message.chat.id,
            message.from_user.id,
            reason,
            WarningLevel.SEVERE if warning_count >= Config.MAX_WARNINGS else WarningLevel.WARNING
        )
        
        if warning_count < Config.MAX_WARNINGS:
            warning_msg = await message.reply(
                f"⚠️ {message.from_user.mention}, your message was deleted because it contains {reason}.\n"
                f"Warnings: {warning_count + 1}/{Config.MAX_WARNINGS}"
            )
            await self.schedule_delete(warning_msg)
        else:
            try:
                await self.app.restrict_chat_member(
                    message.chat.id,
                    message.from_user.id,
                    permissions=types.ChatPermissions()
                )
                ban_msg = await message.reply(
                    f"🚫 {message.from_user.mention} has been muted for {Config.MAX_WARNINGS} warnings!"
                )
            except Exception as e:
                ban_msg = await message.reply(
                    f"⚠️ Failed to restrict {message.from_user.mention} (admin required)"
                )
            await self.schedule_delete(ban_msg)
            await self.db.clear_warnings(message.chat.id, message.from_user.id)
            
        return True
    
    async def schedule_delete(self, message: types.Message, delay: int = None):
        if delay is None:
            delay = Config.DELETE_BOT_REPLIES_AFTER
            
        async def delete_later():
            await asyncio.sleep(delay)
            try:
                await message.delete()
            except:
                pass
                
        asyncio.create_task(delete_later())
