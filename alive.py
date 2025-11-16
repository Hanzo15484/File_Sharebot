import os
import time
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ping import format_uptime, BOT_START_TIME

ALIVE_IMAGE_PATH = ""

async def alive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uptime_seconds = time.time() - BOT_START_TIME
    uptime = format_uptime(uptime_seconds)

    # Direct smallcaps text (no function used)
    caption = (
        "ɪ'ᴍ ᴀʟɪᴠᴇ ʙᴀʙʏ!!\n\n"
        f"ᴜᴘᴛɪᴍᴇ - {uptime}"
    )

    # If image missing -> send text only
    if not ALIVE_IMAGE_PATH or not os.path.exists(ALIVE_IMAGE_PATH):
        await update.message.reply_text(caption, parse_mode="HTML")
        return

    # If image exists -> send image + caption
    try:
        await update.message.reply_photo(
            photo=open(ALIVE_IMAGE_PATH, "rb"),
            caption=caption,
            parse_mode="HTML"
        )
    except:
        await update.message.reply_text(caption, parse_mode="HTML")


alive_command = CommandHandler("alive", alive_handler)
