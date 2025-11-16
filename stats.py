import psutil
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

BOT_START = time.time()


def format_uptime(seconds: float) -> str:
    years, seconds = divmod(seconds, 31536000)
    months, seconds = divmod(seconds, 2628000)
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


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # ---- CPU ----
    try:
        cpu_usage = psutil.cpu_percent(interval=None)
    except Exception:
        cpu_usage = "N/A"

    # ---- RAM ----
    try:
        ram = psutil.virtual_memory()
        ram_used = ram.used // (1024 * 1024)
        ram_total = ram.total // (1024 * 1024)
    except Exception:
        ram_used = ram_total = "N/A"

    # ---- Disk ----
    try:
        disk = psutil.disk_usage('/')
        disk_used = disk.used // (1024 * 1024)
        disk_total = disk.total // (1024 * 1024)
    except Exception:
        disk_used = disk_total = "N/A"

    # ---- Python process RAM ----
    try:
        process = psutil.Process()
        process_ram = process.memory_info().rss // (1024 * 1024)
    except Exception:
        process_ram = "N/A"

    uptime = format_uptime(time.time() - BOT_START)

    text = (
        "*System Stats*\n\n"
        f"💠 *CPU Usage:* {cpu_usage}%\n"
        f"💠 *RAM:* {ram_used} MB / {ram_total} MB\n"
        f"💠 *Disk:* {disk_used} MB / {disk_total} MB\n"
        f"💠 *Bot RAM Usage:* {process_ram} MB\n"
        f"💠 *Uptime:* {uptime}\n"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


stats_command = CommandHandler("stats", stats_handler)
