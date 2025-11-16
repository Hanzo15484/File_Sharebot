# stats.py — /stats with loading animation + advanced system panel

import asyncio
import os
import time
import subprocess
import shutil
from datetime import datetime
from typing import List, Union

try:
    import psutil
except:
    psutil = None

try:
    import requests
except:
    requests = None

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

BOT_START = time.time()


# -------------------------------
# Uptime Formatter
# -------------------------------
def format_uptime(seconds: float) -> str:
    years, seconds = divmod(seconds, 31536000)
    months, seconds = divmod(seconds, 2628000)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if years >= 1: parts.append(f"{int(years)}y")
    if months >= 1: parts.append(f"{int(months)}m")
    if days >= 1: parts.append(f"{int(days)}d")

    parts.append(f"{int(hours)}h")
    parts.append(f"{int(minutes)}min")
    parts.append(f"{int(seconds)}s")

    return ", ".join(parts)


# -------------------------------
# CPU Usage via Termux TOP
# -------------------------------
def get_cpu_usage_termux():
    try:
        output = subprocess.check_output("top -b -n 1", shell=True).decode()
    except:
        return "N/A"

    for line in output.splitlines():
        if "%cpu" in line.lower():
            parts = line.split()
            total = idle = None

            for p in parts:
                if p.endswith("%cpu"):
                    try:
                        total = int(p.replace("%cpu", ""))
                    except:
                        pass
                if p.endswith("%idle"):
                    try:
                        idle = int(p.replace("%idle", ""))
                    except:
                        pass

            if total is not None and idle is not None:
                usage_raw = total - idle
                if total > 100:
                    cores = max(1, total // 100)
                    usage = max(0, min(100, round(usage_raw / cores)))
                else:
                    usage = max(0, min(100, usage_raw))
                return usage
    return "N/A"


# -------------------------------
# CPU Sampling
# -------------------------------
async def sample_cpu(n=7, interval=0.35):
    samples = []
    for _ in range(n):
        usage = await asyncio.to_thread(get_cpu_usage_termux)
        samples.append(usage)
        await asyncio.sleep(interval)
    return samples


# -------------------------------
# Load Chart (Option C)
# -------------------------------
def samples_to_chart(samples):
    blocks = ["▁","▂","▃","▄","▅","▆","▇","█"]
    nums = []
    chart = []

    for s in samples:
        if isinstance(s, int):
            nums.append(f"{s}%")
            idx = min(7, max(0, (s * 7) // 100))
            chart.append(blocks[idx])
        else:
            nums.append("N/A")
            chart.append("·")

    return " → ".join(nums), "".join(chart)


# -------------------------------
# CPU Stress Test
# -------------------------------
async def stress_test():
    end = time.time() + 2

    def burn(t):
        x = 0
        while time.time() < t:
            x ^= (x << 1) & 0xFFFFFFFF
        return x

    task = asyncio.to_thread(burn, end)

    peaks = []
    while time.time() < end:
        u = await asyncio.to_thread(get_cpu_usage_termux)
        peaks.append(u if isinstance(u, int) else 0)
        await asyncio.sleep(0.25)

    await task
    return max(peaks) if peaks else "N/A"


# -------------------------------
# Network Speed Tests
# -------------------------------
async def download_speed():
    if not requests:
        return "N/A", "N/A"
    try:
        url = "https://speed.hetzner.de/1MB.bin"
        t0 = time.time()
        r = requests.get(url, stream=True, timeout=10)
        total = 0
        for chunk in r.iter_content(32768):
            if not chunk: break
            total += len(chunk)
            if total > 1_500_000: break
        t1 = time.time()
        speed = (total / (1024*1024)) / max(0.001, (t1 - t0))
        return round(speed,2), total
    except:
        return "N/A", "N/A"


async def upload_speed():
    if not requests:
        return "N/A", "N/A"
    try:
        payload = os.urandom(600_000)
        t0 = time.time()
        r = requests.post("https://0x0.st", files={"file":("x.bin",payload)}, timeout=15)
        t1 = time.time()
        if r.status_code not in (200,201):
            return "N/A","N/A"
        speed = (len(payload)/(1024*1024)) / max(0.001,(t1 - t0))
        return round(speed,2), len(payload)
    except:
        return "N/A","N/A"


# -------------------------------
# Storage Info
# -------------------------------
def get_storage(path):
    try:
        st = os.statvfs(path)
        total = (st.f_blocks * st.f_frsize)//(1024*1024)
        free = (st.f_bfree * st.f_frsize)//(1024*1024)
        used = total - free
        pct = round((used/total)*100,1)
        return used, total, pct
    except:
        return "N/A","N/A","N/A"


# -------------------------------
# /stats Handler
# -------------------------------
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = await update.message.reply_text("⏳ *Collecting system info…*", parse_mode="Markdown")

    # ---- Basic Info ----
    uptime = format_uptime(time.time() - BOT_START)

    # RAM
    if psutil:
        try:
            r = psutil.virtual_memory()
            ram_used = r.used//(1024*1024)
            ram_total = r.total//(1024*1024)
        except:
            ram_used = ram_total = "N/A"

        try:
            p = psutil.Process()
            bot_ram = p.memory_info().rss//(1024*1024)
        except:
            bot_ram = "N/A"
    else:
        ram_used = ram_total = bot_ram = "N/A"

    await msg.edit_text("🔍 *Checking CPU samples…*", parse_mode="Markdown")

    # ---- CPU Sampling ----
    cpu_samples = await sample_cpu()
    num_line, bar_line = samples_to_chart(cpu_samples)
    base_cpu = cpu_samples[-1]

    await msg.edit_text("🔥 *Running short CPU stress-test…*", parse_mode="Markdown")
    peak_cpu = await stress_test()

    await msg.edit_text("🌐 *Testing network speed…*", parse_mode="Markdown")
    dl_speed, dl_bytes = await download_speed()
    ul_speed, ul_bytes = await upload_speed()

    await msg.edit_text("📦 *Checking storage…*", parse_mode="Markdown")

    # ---- Storage ----
    termux_used, termux_total, termux_pct = get_storage("/data/data/com.termux/files")

    phone_path = None
    for p in ("/storage/emulated/0","/sdcard","/storage/self/primary"):
        if os.path.exists(p):
            phone_path = p
            break
    if not phone_path: phone_path = "/"

    phone_used, phone_total, phone_pct = get_storage(phone_path)

    # ---- Final Report ----
    final = (
        "**📊 System Stats**\n\n"
        f"⏱ **Uptime:** `{uptime}`\n"
        f"💾 **RAM:** `{ram_used} MB / {ram_total} MB`\n"
        f"🧠 **Bot RAM:** `{bot_ram} MB`\n\n"

        f"💽 **Termux Storage:** `{termux_used} / {termux_total} MB` ({termux_pct}%)\n"
        f"📱 **Phone Storage:** `{phone_used} / {phone_total} MB` ({phone_pct}%)\n\n"

        f"🔸 **CPU Baseline:** `{base_cpu}%`\n"
        f"🔸 **CPU Samples:** `{num_line}`\n"
        f"🔸 **Load Chart:** `{bar_line}`\n"
        f"🔸 **Stress-Test Peak:** `{peak_cpu}%`\n\n"

        f"🌐 **Download Speed:** `{dl_speed} MB/s` `{dl_bytes} bytes`\n"
        f"🌐 **Upload Speed:** `{ul_speed} MB/s` `{ul_bytes} bytes`\n"
    )

    await msg.edit_text(final, parse_mode="Markdown")


stats_command = CommandHandler("stats", stats_handler)
