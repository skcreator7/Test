from telethon import TelegramClient, events, Button
from config import Config
import logging
import re
from typing import Dict, List, Any, AsyncGenerator

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db: Any):
        self.db = db
        self.client = TelegramClient(
            'movie_bot',
            Config.API_ID,
            Config.API_HASH
        ).start(bot_token=Config.BOT_TOKEN)
        self._register_handlers()

    async def _search_posts(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Search messages in channel"""
        async for msg in self.client.iter_messages(
            Config.SOURCE_CHANNEL_ID,
            search=query,
            limit=20
        ):
            if msg.text:
                yield await self._parse_post(msg.text, msg.id)

    async def _parse_post(self, text: str, msg_id: int) -> Dict[str, Any]:
        """Parse movie post into structured data"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return {}
        
        data = {
            'title': lines[0],
            'links': {},
            'episodes': {},
            'msg_id': msg_id
        }
        
        current_episode = None
        for line in lines[1:]:
            # Episode detection
            if match := re.match(r'^(Episode|EP)\s*(\d+)', line, re.IGNORECASE):
                current_episode = match.group(2)
                data['episodes'][current_episode] = {}
                continue
                
            # Quality links
            if '🎞️' in line and 'http' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    quality = parts[0].replace('🎞️', '').strip()
                    url = parts[1].strip()
                    if current_episode:
                        data['episodes'][current_episode][quality] = url
                    else:
                        data['links'][quality] = url
        
        return data

    def _register_handlers(self):
        """Register bot event handlers"""

        @self.client.on(events.NewMessage(pattern='/start'))
        async def start(event):
            await event.reply(
                "🎬 Welcome to Movie Search Bot!\n\n"
                "Search for movies/series to get download links\n"
                "Example: `Avengers` or `Mirzapur S01`",
                parse_mode='md'
            )

        @self.client.on(events.NewMessage)
        async def search(event):
            if event.text.startswith('/'):
                return
                
            query = event.text.strip()
            if len(query) < 3:
                return await event.reply("Minimum 3 characters required")
            
            results = []
            async for post in self._search_posts(query):
                if post.get('links') or post.get('episodes'):
                    results.append(post)
            
            if not results:
                return await event.reply("No results found")
            
            # Prepare buttons
            buttons = []
            first = results[0]
            web_url = f"{Config.BASE_URL}/view/{first['msg_id']}?q={query}"
            
            # Add quality buttons
            for quality in ['480p', '720p', '1080p']:
                if quality in first.get('links', {}):
                    buttons.append(Button.url(quality, first['links'][quality]))
            
            # Add web view button
            buttons.append(Button.url("🌐 Web View", web_url))
            
            # Add more results if available
            if len(results) > 1:
                buttons.append(
                    Button.inline(
                        f"More Results ({len(results)-1})", 
                        data=f"more:{query}"
                    )
                )
            
            await event.reply(
                f"🎬 *{first['title']}*",
                buttons=[buttons[i:i+2] for i in range(0, len(buttons), 2)],
                parse_mode='md',
                link_preview=False
            )

        @self.client.on(events.CallbackQuery(data=re.compile(b'^more:')))
        async def more_results(event):
            query = event.data.decode().split(':', 1)[1]
            web_url = f"{Config.BASE_URL}/search?q={query}"
            await event.edit(
                f"🔍 All results for '{query}':\n{web_url}",
                buttons=[[Button.url("Open Web Results", web_url)]]
            )

    async def stop(self):
        await self.client.disconnect()
