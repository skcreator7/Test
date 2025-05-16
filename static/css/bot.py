from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from routes import posts
import re
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
CHANNELS = ["@SKFILMBOX", "@Fmovies_robot", "@SKadminrobot"]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    for channel in CHANNELS:
        try:
            history = await context.bot.get_chat_history(chat_id=channel, limit=50)
            for message in history:
                if query.lower() in (message.text or "").lower():
                    links = re.findall(r'https?://\S+', message.text)
                    post_id = str(message.message_id)
                    posts[post_id] = {
                        "title": query,
                        "links": links
                    }
                    url = f"https://annual-veronique-urlpost-8f671caf.koyeb.app/watch/{post_id}/{query.replace(' ', '_')}"
                    await update.message.reply_text(f"Found in {channel}:
{url}")
                    return
        except Exception as e:
            print(f"Error with {channel}: {e}")

    await update.message.reply_text("No matching post found.")

async def setup_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.initialize()
    await app.start()