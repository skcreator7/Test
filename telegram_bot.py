from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from config import Config
import logging
from typing import List, Dict, AsyncGenerator
import re

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.app = Client(
            "movie_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=Config.WORKERS
        )
        self._register_handlers()

    async def initialize(self):
        await self.app.start()
        me = await self.app.get_me()
        logger.info(f"Bot started as @{me.username}")
        return self

    async def _search_channel_posts(self, query: str) -> AsyncGenerator[Message, None]:
        async for message in self.app.search_messages(
            chat_id=Config.SOURCE_CHANNEL_ID,
            query=query,
            limit=20
        ):
            if message.text:
                yield message

    async def _parse_movie_post(self, text: str) -> Dict:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return {}
        
        movie = {'title': lines[0], 'links': {}, 'episodes': {}}
        
        current_episode = None
        for line in lines[1:]:
            # Check for episode markers
            episode_match = re.match(r'^(Episode|EP)\s*(\d+)', line, re.IGNORECASE)
            if episode_match:
                current_episode = episode_match.group(2)
                movie['episodes'][current_episode] = {}
                continue
                
            # Process quality links
            if '🎞️' in line and 'http' in line and 'youtube' not in line.lower():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    quality = parts[0].replace('🎞️', '').strip()
                    url = parts[1].strip()
                    
                    if current_episode:
                        movie['episodes'][current_episode][quality] = url
                    else:
                        movie['links'][quality] = url
        
        return movie

    async def _generate_web_link(self, post_id: int, query: str = "") -> str:
        return f"{Config.BASE_URL}/view/{post_id}?q={query}"

    def _register_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client, message: Message):
            await message.reply(
                "🎬 Welcome to Movie Search Bot!\n\n"
                "Search for any movie/series and get direct links\n"
                "Example: `Avengers Endgame` or `Mirzapur S01`",
                parse_mode=ParseMode.MARKDOWN
            )

        @self.app.on_message(filters.text & filters.private & ~filters.command)
        async def search_handler(client, message: Message):
            query = message.text.strip()
            if len(query) < 3:
                return await message.reply("Minimum 3 characters required")
            
            results = []
            async for msg in self._search_channel_posts(query):
                post = await self._parse_movie_post(msg.text)
                if post.get('links') or post.get('episodes'):
                    post['msg_id'] = msg.id
                    results.append(post)
            
            if not results:
                return await message.reply("No results found")
            
            # Prepare buttons for first result
            first_result = results[0]
            buttons = []
            web_url = await self._generate_web_link(first_result['msg_id'], query)
            
            # Add quality buttons (max 4)
            for quality in ['480p', '720p HEVC', '720p', '1080p']:
                if quality in first_result.get('links', {}):
                    buttons.append(
                        InlineKeyboardButton(quality, url=first_result['links'][quality])
                    )
            
            # Add web view button
            buttons.append(InlineKeyboardButton("🌐 Web View", url=web_url))
            
            # Add more results button if available
            if len(results) > 1:
                buttons.append(
                    InlineKeyboardButton(
                        f"More Results ({len(results)-1})",
                        callback_data=f"more:{query}"
                    )
                )
            
            # Organize buttons in 2x2 grid
            keyboard = InlineKeyboardMarkup([buttons[i:i+2] for i in range(0, len(buttons), 2)])
            
            await message.reply(
                f"🎬 *{first_result['title']}*\n"
                "Choose quality option:",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )

        @self.app.on_callback_query(filters.regex("^more:"))
        async def more_results_handler(client, callback_query):
            query = callback_query.data.split(":", 1)[1]
            web_url = f"{Config.BASE_URL}/search?q={query}"
            
            await callback_query.message.reply(
                f"🔍 All results for '{query}' available on web:\n{web_url}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Open Web Results", url=web_url)
                ]]),
                disable_web_page_preview=True
            )
            await callback_query.answer()

    async def stop(self):
        await self.app.stop()
        logger.info("Bot stopped")
