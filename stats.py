import psutil
import time
import subprocess
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


def get_cpu_usage():
    try:
        output = subprocess.check_output(
            "top -b -n 1", shell=True
        ).decode()

        for line in output.split("\n"):
            if "%cpu" in line.lower():
                # Example from your device:
                # 800%cpu 0%user 0%nice 0%sys 800%idle ...
                parts = line.split()

                total = idle = None

                for p in parts:
                    if p.endswith("%cpu"):
                        total = int(p.replace("%cpu", ""))
                    if p.endswith("%idle"):
                        idle = int(p.replace("%idle", ""))

                if total is not None and idle is not None:
                    usage = total - idle
                    if usage < 0:
                        usage = 0
                    return usage

        return "N/A"

    except Exception:
        return "N/A"


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # CPU
    cpu_usage = get_cpu_usage()

    # RAM
    try:
        ram = psutil.virtual_memory()
        ram_used = ram.used // (1024 * 1024)
        ram_total = ram.total // (1024 * 1024)
    except:
        ram_used = ram_total = "N/A"

    # Disk
    try:
        disk = psutil.disk_usage('/')
        disk_used = disk.used // (1024 * 1024)
        disk_total = disk.total // (1024 * 1024)
    except:
        disk_used = disk_total = "N/A"

    # Bot RAM
    try:
        process = psutil.Process()
        process_ram = process.memory_info().rss // (1024 * 1024)
    except:
        process_ram = "N/A"

    uptime = format_uptime(time.time() - BOT_START)

    text = (
        "**📊 System Stats**\n\n"
        f"💠 **CPU Usage:** `{cpu_usage}%`\n"
        f"💠 **RAM:** `{ram_used} MB / {ram_total} MB`\n"
        f"💠 **Disk:** `{disk_used} MB / {disk_total} MB`\n"
        f"💠 **Bot RAM Usage:** `{process_ram} MB`\n"
        f"💠 **Uptime:** `{uptime}`\n"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


stats_command = CommandHandler("stats", stats_handler)
