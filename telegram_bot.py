from telethon import TelegramClient, events, Button
from telethon.tl.types import InputPeerChannel
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
        self.client = TelegramClient(
            'movie_bot',
            Config.API_ID,
            Config.API_HASH,
            base_logger=logger
        ).start(bot_token=Config.BOT_TOKEN)
        self._register_handlers()

    async def initialize(self) -> 'TelegramBot':
        """Start the bot and initialize resources"""
        try:
            me = await self.client.get_me()
            await Config.update_channel_info(self.client)
            logger.info(f"Bot started as @{me.username}")
            return self
        except Exception as e:
            logger.critical(f"Bot initialization failed: {e}")
            raise

    async def _get_input_peer_channel(self) -> InputPeerChannel:
        """Get InputPeerChannel for the source channel"""
        try:
            chat = await self.client.get_entity(Config.SOURCE_CHANNEL_ID)
            await self.db.update_channel_hash(chat.id, chat.access_hash)
            return InputPeerChannel(
                channel_id=chat.id,
                access_hash=chat.access_hash
            )
        except Exception as e:
            logger.warning(f"Failed to get fresh channel info: {str(e)}")
            doc = await self.db.channels.find_one({'_id': Config.SOURCE_CHANNEL_ID})
            if doc:
                return InputPeerChannel(
                    channel_id=doc['_id'],
                    access_hash=doc['access_hash']
                )
            raise ConnectionError("Could not retrieve channel information")

    async def _search_channel_posts(self, query: str) -> AsyncGenerator[Any, None]:
        """Search messages in the source channel"""
        async for message in self.client.iter_messages(
            Config.SOURCE_CHANNEL_ID,
            search=query,
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

        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            """Handle /start command"""
            await event.reply(
                "🎬 Welcome to Movie Search Bot!\n\n"
                "Search for any movie/series and get direct links\n"
                "Example: `Avengers Endgame` or `Mirzapur S01`",
                parse_mode='md'
            )

        @self.client.on(events.NewMessage())
        async def search_handler(event):
            """Handle search queries"""
            try:
                if event.text.startswith('/'):
                    return
                    
                query = event.text.strip()
                if len(query) < 3:
                    await event.reply("Minimum 3 characters required")
                    return
                
                results: List[Dict[str, Any]] = []
                async for msg in self._search_channel_posts(query):
                    post = await self._parse_movie_post(msg.text)
                    if post.get('links') or post.get('episodes'):
                        post['msg_id'] = msg.id
                        results.append(post)
                
                if not results:
                    await event.reply("No results found")
                    return
                
                first_result = results[0]
                buttons = []
                web_url = await self._generate_web_link(first_result['msg_id'], query)
                
                # Add quality buttons
                for quality in ['480p', '720p HEVC', '720p', '1080p']:
                    if quality in first_result.get('links', {}):
                        buttons.append(
                            Button.url(quality, first_result['links'][quality])
                        )
                
                # Add web view button
                buttons.append(Button.url("🌐 Web View", web_url))
                
                # Add more results button if available
                if len(results) > 1:
                    buttons.append(
                        Button.inline(
                            f"More Results ({len(results)-1})",
                            data=f"more:{query}"
                        )
                    )
                
                # Organize buttons in 2x2 grid
                keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
                
                await event.reply(
                    f"🎬 *{first_result['title']}*\n"
                    "Choose quality option:",
                    buttons=keyboard,
                    parse_mode='md',
                    link_preview=False
                )
            except Exception as e:
                logger.error(f"Search handler error: {e}")
                await event.reply("An error occurred while processing your request")

        @self.client.on(events.CallbackQuery(data=re.compile(b'^more:')))
        async def more_results_handler(event):
            """Handle 'more results' callback"""
            try:
                query = event.data.decode().split(":", 1)[1]
                web_url = f"{Config.BASE_URL}/search?q={query}"
                
                await event.edit(
                    f"🔍 All results for '{query}' available on web:\n{web_url}",
                    buttons=[
                        [Button.url("Open Web Results", web_url)]
                    ],
                    link_preview=False
                )
            except Exception as e:
                logger.error(f"More results handler error: {e}")
                await event.answer("An error occurred", alert=True)

    async def stop(self) -> None:
        """Stop the bot gracefully"""
        try:
            await self.client.disconnect()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            raise
