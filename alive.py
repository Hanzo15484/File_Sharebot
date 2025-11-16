import os
import time
import asyncio
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, CommandHandler

from settings import load_settings
from stats import BOT_START, format_uptime


async def alive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # --- internal speed check ---
    bot_start = time.time()

    waiting_msg = await update.message.reply_text(
        "ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 3"
    )

    internal_ping = int((time.time() - bot_start) * 1000)


    # --- calculate status based on internal speed ---
    if internal_ping <= 50:
        status = "🟢 ꜰᴀsᴛ"
    elif internal_ping <= 150:
        status = "🟡 sʟᴏᴡ"
    else:
        status = "🔴 ᴅᴇʟᴀʏᴇᴅ"


    # --- countdown animation ---
    try:
        await asyncio.sleep(1)
        await waiting_msg.edit_text("ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 2")
        await asyncio.sleep(1)
        await waiting_msg.edit_text("ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 1")
        await asyncio.sleep(1)
    except:
        pass

    # --- alive details ---
    settings = load_settings()
    alive_image = settings.get("alive_image", "")

    uptime = format_uptime(time.time() - BOT_START)

    caption = (
        "ɪ'ᴍ ᴀʟɪᴠᴇ ʙᴀʙʏ!!\n\n"
        f"ᴜᴘᴛɪᴍᴇ: {uptime}\n"
        f"ʀᴇsᴘᴏɴsᴇ: {internal_ping} ᴍs\n"
        f"sᴛᴀᴛᴜs: {status}"
    )

    # --- send image or fallback ---
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
            pass

    await waiting_msg.edit_text(caption)


alive_command = CommandHandler("alive", alive_handler)
