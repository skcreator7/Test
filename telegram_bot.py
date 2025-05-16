from pyrogram import Client
import asyncio
from config import Config
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
            workers=2,
            sleep_threshold=30,
            in_memory=True
        )
        self._running = False

    async def start(self):
        """Start the bot with enhanced connection handling"""
        self._running = True
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                await self.app.start()
                logger.info(f"🤖 Bot started monitoring channel: {Config.SOURCE_CHANNEL_ID}")
                asyncio.create_task(self.connection_monitor())
                return True
            except Exception as e:
                logger.error(f"🚨 Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("🔥 All connection attempts failed")
                    return False

    async def connection_monitor(self):
        """Enhanced connection monitor with exponential backoff"""
        retry_count = 0
        max_retries = 5
        base_delay = 5
        
        while self._running:
            try:
                if not await self.app.is_connected():
                    retry_count += 1
                    delay = min(base_delay * (2 ** (retry_count - 1)), 300)  # Max 5 min delay
                    logger.warning(f"⚠️ Bot disconnected. Attempting reconnect #{retry_count} in {delay}s")
                    
                    await asyncio.sleep(delay)
                    await self.app.start()
                    retry_count = 0
                    logger.info("✅ Reconnection successful")
            except Exception as e:
                logger.error(f"Connection monitor error: {str(e)}")
            finally:
                await asyncio.sleep(60)  # Normal check interval

    async def stop(self):
        """Graceful shutdown with proper cleanup"""
        self._running = False
        try:
            if await self.app.is_connected():
                await self.app.stop()
                logger.info("✅ Bot stopped cleanly")
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
        finally:
            # Clean up any other resources
            pass
