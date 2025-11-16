# alive.py

import os
import time
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from settings import load_settings
from stats import BOT_START, format_uptime  # You already have uptime formatter

async def alive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    settings = load_settings()
    alive_image = settings.get("alive_image", "")

    # Uptime
    uptime_seconds = time.time() - BOT_START
    uptime_text = format_uptime(uptime_seconds)

    caption = (
        "ɪ'ᴍ ᴀʟɪᴠᴇ ʙᴀʙʏ!!\n\n"
        f"ᴜᴘᴛɪᴍᴇ: {uptime_text}"
    )

    # If alive image exists
    if alive_image and os.path.exists(alive_image):
        await update.message.reply_photo(
            photo=open(alive_image, "rb"),
            caption=caption
        )
        return

    # Fallback no image
    await update.message.reply_text(caption)

alive_command = CommandHandler("alive", alive_handler)
