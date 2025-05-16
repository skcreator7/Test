from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database import save_post, search_posts
import re
import logging

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.app = Client(
            "my_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=Config.WORKERS
        )
        
        # Register handlers
        self.app.on_message(filters.chat(Config.MONITORED_CHATS))(self.handle_message)
        self.app.on_message(filters.group & ~filters.service)(self.moderate_group)

    async def handle_message(self, client: Client, message: Message):
        """Save channel posts to database"""
        try:
            post_data = {
                "chat_id": message.chat.id,
                "message_id": message.id,
                "text": message.text or message.caption or "",
                "date": message.date,
                "media": bool(message.media)
            }
            await save_post(self.db, post_data)
            logger.info(f"Saved post {message.id} from {message.chat.title}")
        except Exception as e:
            logger.error(f"Error saving post: {e}")

    async def moderate_group(self, client: Client, message: Message):
        """Delete messages containing links or mentions"""
        try:
            text = message.text or message.caption or ""
            
            # Check for violations
            if re.search(r'https?://|@\w+', text):
                await message.delete()
                logger.info(f"Deleted spam message in {message.chat.title}")
                
                # Warn user
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"@{message.from_user.username} Please don't post links or mentions!",
                    reply_to_message_id=message.id
                )
        except Exception as e:
            logger.error(f"Moderation error: {e}")

    # ... (keep existing start/stop methods from previous solution)
