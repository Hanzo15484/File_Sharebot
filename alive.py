import os
import time
import asyncio
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, CommandHandler

from settings import load_settings
from stats import BOT_START, format_uptime


async def alive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 1. Send instant message with smallcaps countdown header
    waiting_msg = await update.message.reply_text(
        "ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 3"
    )

    # 2. Background preparation
    settings = load_settings()
    alive_image = settings.get("alive_image", "")

    uptime = format_uptime(time.time() - BOT_START)

    caption = (
        "ɪ'ᴍ ᴀʟɪᴠᴇ ʙᴀʙʏ!!\n\n"
        f"ᴜᴘᴛɪᴍᴇ: {uptime}"
    )

    # 3. Countdown animation (3 → 2 → 1)
    try:
        await asyncio.sleep(1)
        await waiting_msg.edit_text("ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 2")

        await asyncio.sleep(1)
        await waiting_msg.edit_text("ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 1")

        await asyncio.sleep(1)
    except:
        pass

    # 4. Edit final alive message with image (if exists)
    if alive_image and os.path.exists(alive_image):
        try:
            await waiting_msg.edit_media(
                InputMediaPhoto(
                    media=open(alive_image, "rb"),
                    caption=caption
                )
            )
            return
        except:
            pass  # fallback to text

    # 5. Fallback to text if image broken or missing
    await waiting_msg.edit_text(caption)


alive_command = CommandHandler("alive", alive_handler)
