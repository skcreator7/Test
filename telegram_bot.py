from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
import logging
import os
import re
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.user_session = os.getenv("USER_SESSION_STRING")
        if not self.user_session:
            raise ValueError("USER_SESSION_STRING is required for channel scraping")

        self.user_client = Client(
            name="movie_scraper",
            session_string=self.user_session,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH
        )
        self.bot_client = Client(
            name="movie_bot",
            bot_token=Config.BOT_TOKEN,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH
        )
        self._register_handlers()
        self.scrape_interval = timedelta(seconds=Config.SCRAPE_INTERVAL)

    async def initialize(self):
        await self.user_client.start()
        await self.bot_client.start()
        me = await self.bot_client.get_me()
        logger.info(f"Bot started as @{me.username}")
        user = await self.user_client.get_me()
        logger.info(f"User client started as @{user.username}")
        asyncio.create_task(self._periodic_scrape())
        return self

    async def _periodic_scrape(self):
        while True:
            try:
                await self._scrape_channels()
                logger.info(f"Channel scrape completed. Next in {self.scrape_interval}")
            except Exception as e:
                logger.error(f"Scraping failed: {e}")
            await asyncio.sleep(self.scrape_interval.total_seconds())

    async def _scrape_channels(self):
        channels = await self.db.get_channels_to_scrape()
        if not channels:
            logger.info("No channels to scrape")
            return
        for channel in channels:
            try:
                last_scraped = channel.get('last_scraped') or datetime(1970, 1, 1)
                new_posts = 0
                logger.info(f"Scraping channel {channel['name']} (ID: {channel['channel_id']})")
                async for message in self.user_client.get_chat_history(
                    chat_id=channel['channel_id'],
                    limit=100
                ):
                    if message.date < last_scraped:
                        break
                    if not (message.document or (message.text and any(
                        kw in message.text.lower()
                        for kw in ['movie', 'film', 'download', 'watch']
                    ))):
                        continue
                    post_data = self._process_message(message)
                    await self.db.upsert_post(
                        channel_id=channel['channel_id'],
                        message_id=message.id,
                        data=post_data
                    )
                    new_posts += 1
                await self.db.update_channel_scrape_status(
                    channel_id=channel['channel_id'],
                    last_scraped=datetime.utcnow(),
                    status='success',
                    new_posts=new_posts
                )
                logger.info(f"Found {new_posts} new posts in {channel['name']}")
            except Exception as e:
                logger.error(f"Failed to scrape channel {channel['name']}: {e}")
                await self.db.update_channel_scrape_status(
                    channel_id=channel['channel_id'],
                    last_scraped=datetime.utcnow(),
                    status='failed',
                    error=str(e)
                )

    def _process_message(self, message: Message):
        return {
            'title': self._extract_title(message),
            'description': self._extract_description(message),
            'size': self._format_size(message),
            'links': self._extract_links(message),
            'message_id': message.id,
            'date': message.date,
            'views': getattr(message, 'views', 0),
            'scraped_at': datetime.utcnow(),
            'media_type': self._get_media_type(message)
        }

    def _get_media_type(self, message: Message) -> str:
        if message.document:
            return 'document'
        elif message.video:
            return 'video'
        elif message.audio:
            return 'audio'
        elif message.photo:
            return 'photo'
        return 'text'

    def _extract_title(self, message: Message) -> str:
        if message.caption:
            return message.caption.split("\n")[0].strip()
        elif message.text:
            return message.text.split("\n")[0].strip()
        return "Untitled"

    def _extract_description(self, message: Message) -> str:
        if message.caption:
            return "\n".join(message.caption.split("\n")[1:]).strip()
        elif message.text:
            return "\n".join(message.text.split("\n")[1:]).strip()
        return "No description"

    def _format_size(self, message: Message) -> str:
        if message.document:
            size = message.document.file_size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size/(1024*1024):.1f} MB"
            else:
                return f"{size/(1024*1024*1024):.1f} GB"
        return ""

    def _extract_links(self, message: Message):
        text = message.caption or message.text or ""
        url_pattern = re.compile(
            r'(https?://(?:www\.)?(?:mega\.nz|gofile\.io|mediafire\.com|drive\.google\.com|zippyshare\.com|1fichier\.com)[^\s]+)',
            re.IGNORECASE
        )
        return url_pattern.findall(text)

    def _register_handlers(self):
        @self.bot_client.on_message(filters.command("start") & filters.private)
        async def start_handler(client, message: Message):
            await message.reply(
                "🎬 Welcome to Movie Search Bot!\n\n"
                "Search for movies from our private channels\n"
                "Example: `Animal 2023` or `Oppenheimer`\n\n"
                "Admin commands:\n"
                "/add_channel - Add new channel to scrape\n"
                "/list_channels - Show monitored channels",
                parse_mode="markdown"
            )

        @self.bot_client.on_message(filters.command("add_channel") & filters.user(Config.ADMINS))
        async def add_channel_handler(client, message: Message):
            try:
                if len(message.command) < 2:
                    await message.reply("Usage: /add_channel <channel_id> <name>")
                    return

                channel_id = int(message.command[1])
                name = ' '.join(message.command[2:]) or f"Channel {channel_id}"
                try:
                    chat = await self.user_client.get_chat(channel_id)
                    if not chat:
                        await message.reply("Could not access channel. Make sure the user is a member.")
                        return
                except Exception as e:
                    await message.reply(f"Failed to access channel: {e}")
                    return
                await self.db.add_channel({
                    'channel_id': channel_id,
                    'name': name,
                    'added_by': message.from_user.id,
                    'added_at': datetime.utcnow(),
                    'last_scraped': None,
                    'scrape_status': 'pending'
                })
                await message.reply(f"✅ Channel added: {name} (ID: {channel_id})")
                asyncio.create_task(self._scrape_channels())
            except Exception as e:
                await message.reply(f"Error adding channel: {e}")

        @self.bot_client.on_message(filters.command("list_channels") & filters.user(Config.ADMINS))
        async def list_channels_handler(client, message: Message):
            channels = await self.db.get_channels()
            if not channels:
                await message.reply("No channels configured")
                return

            response = ["📺 Monitored Channels:"]
            for channel in channels:
                status = f"🟢 {channel['scrape_status']}" if channel['scrape_status'] == 'success' else f"🔴 {channel['scrape_status']}"
                last_scraped = channel.get('last_scraped', 'Never')
                if isinstance(last_scraped, datetime):
                    last_scraped = last_scraped.strftime('%Y-%m-%d %H:%M')
                response.append(
                    f"{status} {channel['name']} (ID: {channel['channel_id']})\n"
                    f"Last scraped: {last_scraped}\n"
                    f"Posts: {channel.get('post_count', 0)}"
                )
            await message.reply("\n\n".join(response))

        @self.bot_client.on_message(filters.text & filters.private & ~filters.regex(r"^/"))
        async def search_handler(client, message: Message):
            query = message.text.strip()
            if len(query) < 3:
                await message.reply("Please enter at least 3 characters to search")
                return
            try:
                await message.reply_chat_action("typing")
                results = await self.db.search_posts(query)
                if not results:
                    await message.reply("No results found. Try different keywords")
                    return
                response = ["🔍 Search Results:"]
                for idx, result in enumerate(results[:5], 1):
                    links = "\n".join([f"🔗 {link}" for link in result['links'][:2]]) if result.get('links') else ""
                    response.append(
                        f"{idx}. **{result['title']}**\n"
                        f"📅 {result['date'].strftime('%b %d, %Y')}\n"
                        f"📦 {result.get('size', '')}\n"
                        f"{links}"
                    )
                await message.reply(
                    "\n\n".join(response),
                    parse_mode="markdown",
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Search error: {e}", exc_info=True)
                await message.reply("Error searching. Please try again later")

    async def stop(self):
        await self.user_client.stop()
        await self.bot_client.stop()
        logger.info("All clients stopped")
