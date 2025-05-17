from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from pyrogram import raw
from config import Config
import logging
import re
from typing import Dict, List, Any, Optional, AsyncGenerator

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db: Any) -> None:
        """
        Initialize Telegram bot
        Args:
            db: Database instance
        """
        self.db = db
        self.app = Client(
            "movie_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=Config.WORKERS,
            sleep_threshold=30
        )
        self._register_handlers()

    async def initialize(self) -> 'TelegramBot':
        """Start the bot and initialize resources"""
        try:
            await self.app.start()
            me = await self.app.get_me()
            await Config.update_channel_info(self.app)
            logger.info(f"Bot started as @{me.username}")
            return self
        except Exception as e:
            logger.critical(f"Bot initialization failed: {e}")
            raise

    async def _get_input_peer_channel(self) -> raw.types.InputPeerChannel:
        """Get InputPeerChannel for the source channel"""
        return await self.db.get_channel_peer(self)

    async def _search_channel_posts(self, query: str) -> AsyncGenerator[Message, None]:
        """Search messages in the source channel"""
        async for message in self.app.search_messages(
            chat_id=Config.SOURCE_CHANNEL_ID,
            query=query,
            limit=20
        ):
            if message.text:
                yield message

    async def _parse_movie_post(self, text: str) -> Dict[str, Any]:
        """
        Parse movie post text into structured data
        Args:
            text: Raw post text
        Returns:
            Parsed movie data dictionary
        """
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
        """Generate web view URL for a post"""
        return f"{Config.BASE_URL}/view/{post_id}?q={query}"

    def _register_handlers(self) -> None:
        """Register all bot message handlers"""

        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client: Client, message: Message) -> None:
            """Handle /start command"""
            await message.reply(
                "🎬 Welcome to Movie Search Bot!\n\n"
                "Search for any movie/series and get direct links\n"
                "Example: `Avengers Endgame` or `Mirzapur S01`",
                parse_mode=ParseMode.MARKDOWN
            )

        @self.app.on_message(
            filters.text 
            & filters.private 
            & filters.create(
                lambda _, __, m: not m.text.startswith('/')
            )
        )
        async def search_handler(client: Client, message: Message) -> None:
            """Handle search queries"""
            try:
                query = message.text.strip()
                if len(query) < 3:
                    await message.reply("Minimum 3 characters required")
                    return
                
                results: List[Dict[str, Any]] = []
                async for msg in self._search_channel_posts(query):
                    post = await self._parse_movie_post(msg.text)
                    if post.get('links') or post.get('episodes'):
                        post['msg_id'] = msg.id
                        results.append(post)
                
                if not results:
                    await message.reply("No results found")
                    return
                
                first_result = results[0]
                buttons = []
                web_url = await self._generate_web_link(first_result['msg_id'], query)
                
                # Add quality buttons
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
            except Exception as e:
                logger.error(f"Search handler error: {e}")
                await message.reply("An error occurred while processing your request")

        @self.app.on_callback_query(filters.regex("^more:"))
        async def more_results_handler(client: Client, callback_query: Any) -> None:
            """Handle 'more results' callback"""
            try:
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
            except Exception as e:
                logger.error(f"More results handler error: {e}")
                await callback_query.answer("An error occurred", show_alert=True)

    async def stop(self) -> None:
        """Stop the bot gracefully"""
        try:
            await self.app.stop()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            raise
