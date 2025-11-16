import psutil
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

# Reset every restart
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

    # CPU
    cpu_usage = psutil.cpu_percent(interval=0.4)

    # RAM
    ram = psutil.virtual_memory()
    ram_used = ram.used // (1024 * 1024)
    ram_total = ram.total // (1024 * 1024)

    # Disk
    disk = psutil.disk_usage('/')
    disk_used = disk.used // (1024 * 1024)
    disk_total = disk.total // (1024 * 1024)

    # Python process RAM
    process = psutil.Process()
    process_ram = process.memory_info().rss // (1024 * 1024)

    uptime = format_uptime(time.time() - BOT_START)

    text = (
        "<b>📊 System Stats</b>\n\n"
        f"💠 <b>CPU Usage:</b> {cpu_usage}%\n"
        f"💠 <b>RAM:</b> {ram_used} MB / {ram_total} MB\n"
        f"💠 <b>Disk:</b> {disk_used} MB / {disk_total} MB\n"
        f"💠 <b>Bot RAM Usage:</b> {process_ram} MB\n"
        f"💠 <b>Uptime:</b> {uptime}\n"
    )

    await update.message.reply_text(text, parse_mode="HTML")


stats_command = CommandHandler("stats", stats_handler)
