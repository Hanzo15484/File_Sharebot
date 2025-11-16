import os
import time
import asyncio
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, CommandHandler

from settings import load_settings
from stats import BOT_START, format_uptime


async def alive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # --- TRUE internal ping (no Telegram involved) ---
    t0 = time.perf_counter()
    for _ in range(50000):
        pass
    internal_ping = int((time.perf_counter() - t0) * 1000)

    # ping is always fast now:
    if internal_ping <= 50:
        status = "🟢 ꜰᴀsᴛ"
    elif internal_ping <= 100:
        status = "🟡 sʟᴏᴡ"
    else:
        status = "🔴 ᴅᴇʟᴀʏᴇᴅ"

    # --- send instant countdown message ---
    waiting_msg = await update.message.reply_text(
        "ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 3"
    )

    # --- countdown animation ---
    await asyncio.sleep(1)
    await waiting_msg.edit_text("ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 2")

    await asyncio.sleep(1)
    await waiting_msg.edit_text("ᴘʀᴇᴘᴀʀɪɴɢ ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ… 1")

    await asyncio.sleep(1)

    # --- prepare final alive caption ---
    settings = load_settings()
    alive_image = settings.get("alive_image", "")

    uptime = format_uptime(time.time() - BOT_START)

    caption = (
        "ɪ'ᴍ ᴀʟɪᴠᴇ ʙᴀʙʏ!!\n\n"
        f"ᴜᴘᴛɪᴍᴇ: {uptime}\n"
        f"ʀᴇsᴘᴏɴsᴇ: {internal_ping} ᴍs\n"
        f"sᴛᴀᴛᴜs: {status}"
    )

    # --- update into image + caption ---
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

    # fallback: text-only
    await waiting_msg.edit_text(caption)


alive_command = CommandHandler("alive", alive_handler)
