import os
import time
import asyncio
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, CommandHandler

from settings import load_settings
from stats import BOT_START, format_uptime


async def alive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # ---- start preparing instantly ----
    prep_start = time.time()

    # internal ping
    t0 = time.perf_counter()
    for _ in range(50000):
        pass
    internal_ping = int((time.perf_counter() - t0) * 1000)

    # status light
    if internal_ping <= 20:
        status = "🟢 ꜰᴀsᴛ"
    elif internal_ping <= 60:
        status = "🟡 sʟᴏᴡ"
    else:
        status = "🔴 ᴅᴇʟᴀʏᴇᴅ"

    # send quick placeholder
    waiting_msg = await update.message.reply_text(
        "ᴄʜᴇᴄᴋɪɴɢ ʙᴏᴛ ɪs ᴀʟɪᴠᴇ ᴏʀ ɴᴏᴛ?...",
        parse_mode="MarkdownV2"
    )

    # prepare uptime + caption
    settings = load_settings()
    alive_image = settings.get("alive_image", "")
    uptime = format_uptime(time.time() - BOT_START)

    # escape commas for MarkdownV2
    uptime_md = uptime.replace(",", "\\,")

    caption = (
        "> ɪ'ᴍ ᴀʟɪᴠᴇ ʙᴀʙʏ\\!\\!\n\n"
        f"ᴜᴘᴛɪᴍᴇ\\: {uptime_md}\n"
        f"ʀᴇsᴘᴏɴsᴇ\\: {internal_ping} ᴍs\n"
        f"sᴛᴀᴛᴜs\\: {status}"
    )

    # ---- preparation finished ----
    prep_time = time.time() - prep_start

    # 👉 if preparation was FAST → edit immediately
    if prep_time < 1.2:
        try:
            if alive_image and os.path.exists(alive_image):
                await waiting_msg.edit_media(
                    InputMediaPhoto(
                        media=open(alive_image, "rb"),
                        caption=caption,
                        parse_mode="MarkdownV2"
                    )
                )
                return
        except:
            pass
        
        await waiting_msg.edit_text(caption, parse_mode="MarkdownV2")
        return

    # 👉 if preparation was SLOW → show countdown
    try:
        await waiting_msg.edit_text("ᴄʜᴇᴄᴋɪɴɢ ʙᴏᴛ ɪs ᴀʟɪᴠᴇ ᴏʀ ɴᴏᴛ?... 3", parse_mode="MarkdownV2")
        await asyncio.sleep(1)
        await waiting_msg.edit_text("ᴄʜᴇᴄᴋɪɴɢ ʙᴏᴛ ɪs ᴀʟɪᴠᴇ ᴏʀ ɴᴏᴛ?... 2", parse_mode="MarkdownV2")
        await asyncio.sleep(1)
        await waiting_msg.edit_text("ᴄʜᴇᴄᴋɪɴɢ ʙᴏᴛ ɪs ᴀʟɪᴠᴇ ᴏʀ ɴᴏᴛ?... 1", parse_mode="MarkdownV2")
        await asyncio.sleep(1)
    except:
        pass

    # final output
    try:
        if alive_image and os.path.exists(alive_image):
            await waiting_msg.edit_media(
                InputMediaPhoto(
                    media=open(alive_image, "rb"),
                    caption=caption,
                    parse_mode="MarkdownV2"
                )
            )
            return
    except:
        pass

    await waiting_msg.edit_text(caption, parse_mode="MarkdownV2")


alive_command = CommandHandler("alive", alive_handler)
