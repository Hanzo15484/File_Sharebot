# alive.py

import os
import time
import asyncio
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, CommandHandler

from settings import load_settings
from stats import BOT_START, format_uptime


async def alive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # -------- Step 1: measure ping --------
    start = time.time()

    waiting_msg = await update.message.reply_text(
        "ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 3"
    )

    ping_ms = int((time.time() - start) * 1000)


    # -------- Step 2: determine status light --------
    if ping_ms <= 250:
        status = "🟢 ᴏɴʟɪɴᴇ"
    elif ping_ms <= 800:
        status = "🟡 sʟᴏᴡ"
    else:
        status = "🔴 ᴅᴇʟᴀʏᴇᴅ"


    # -------- Step 3: countdown animation --------
    try:
        await asyncio.sleep(1)
        await waiting_msg.edit_text("ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 2")

        await asyncio.sleep(1)
        await waiting_msg.edit_text("ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 1")

        await asyncio.sleep(1)
    except:
        pass


    # -------- Step 4: prepare alive data --------
    settings = load_settings()
    alive_image = settings.get("alive_image", "")

    uptime = format_uptime(time.time() - BOT_START)

    caption = (
        "ɪ'ᴍ ᴀʟɪᴠᴇ ʙᴀʙʏ!!\n\n"
        f"ᴜᴘᴛɪᴍᴇ: {uptime}\n"
        f"ᴘɪɴɢ: {ping_ms} ᴍs\n"
        f"sᴛᴀᴛᴜs: {status}"
    )


    # -------- Step 5: send final alive message --------
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
            pass  # Fallback to text if edit_media fails


    # Fallback: text-only alive
    await waiting_msg.edit_text(caption)


alive_command = CommandHandler("alive", alive_handler)
