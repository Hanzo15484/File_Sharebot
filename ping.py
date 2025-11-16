import time
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

BOT_START_TIME = time.time()   # resets after every restart


def format_uptime(seconds: float) -> str:
    # Convert seconds → y,m,d,h,min,s
    years, seconds = divmod(seconds, 31536000)   # 365 days
    months, seconds = divmod(seconds, 2628000)   # 1 month avg
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if years >= 1:
        parts.append(f"{int(years)}y")
    if months >= 1:
        parts.append(f"{int(months)}m")
    if days >= 1:
        parts.append(f"{int(days)}d")

    parts.append(f"{int(hours)}h")
    parts.append(f"{int(minutes)}min")
    parts.append(f"{int(seconds)}s")

    return ", ".join(parts)


async def ping_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    start = time.time()

    # Initial message
    msg = await update.message.reply_text("🏓 *ᴘɪɴɢɪɴɢ...*", parse_mode="Markdown")

    await asyncio.sleep(0.3)

    end = time.time()
    ping_ms = (end - start) * 1000
    response_sec = end - start

    uptime_sec = time.time() - BOT_START_TIME
    uptime_text = format_uptime(uptime_sec)

    text = (
        f"🏓**Pong!**\n"
        f"**Ping:** `{ping_ms:.2f} ms`\n"
        f"**Response Time:** `{response_sec:.2f} s`\n"
        f"**Received Message In:** `{response_sec:.2f} s`\n"
        f"**Uptime:** `{uptime_text}`\n\n"
        f"**Pinged by:** <a href=\"tg://user?id={user.id}\">{user.full_name}</a>"
    )

    await msg.edit_text(text, parse_mode="HTML")


ping_command = CommandHandler("ping", ping_handler)
