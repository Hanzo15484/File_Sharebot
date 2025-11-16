import asyncio
import os
import time
import subprocess
import shutil
import math
from datetime import datetime
from typing import List, Tuple, Union

# Optional libs
try:
    import psutil
except Exception:
    psutil = None

try:
    import requests
except Exception:
    requests = None

# speedtest library optional (fallback)
try:
    import speedtest
except Exception:
    speedtest = None

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

# Bot start timestamp (resets on restart)
BOT_START = time.time()

# -----------------------
# Utilities
# -----------------------
def human_readable_bytes(n_bytes: int) -> str:
    if not isinstance(n_bytes, (int, float)):
        return "N/A"
    n = float(n_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"

def format_uptime(seconds: float) -> str:
    if seconds is None:
        return "N/A"
    years, seconds = divmod(int(seconds), 31536000)
    months, seconds = divmod(seconds, 2628000)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if years:
        parts.append(f"{years}y")
    if months:
        parts.append(f"{months}m")
    if days:
        parts.append(f"{days}d")

    parts.append(f"{hours}h")
    parts.append(f"{minutes}min")
    parts.append(f"{seconds}s")
    return ", ".join(parts)

# -----------------------
# CPU detection helpers
# -----------------------
def parse_top_cpu_line(line: str) -> Union[int, None]:
    """
    Parse top line like:
    '800%cpu   0%user   0%nice   0%sys 800%idle ...'
    Compute normalized 0-100% usage.
    """
    try:
        parts = line.split()
        total = idle = None
        for p in parts:
            p = p.strip()
            if p.endswith("%cpu"):
                total = int(p.replace("%cpu","").strip())
            if p.endswith("%idle"):
                idle = int(p.replace("%idle","").strip())
        if total is None or idle is None:
            return None
        usage_raw = total - idle
        if total > 100:
            cores = max(1, total // 100)
            usage_percent = max(0, min(100, round(usage_raw / cores)))
        else:
            usage_percent = max(0, min(100, usage_raw))
        return usage_percent
    except Exception:
        return None

def get_cpu_usage_from_top() -> Union[int,str]:
    """Run top once and parse CPU line. Return percent 0-100 or 'N/A'."""
    try:
        out = subprocess.check_output("top -b -n 1", shell=True, stderr=subprocess.DEVNULL).decode(errors="ignore")
        for line in out.splitlines():
            if "%cpu" in line.lower():
                val = parse_top_cpu_line(line)
                return val if val is not None else "N/A"
    except Exception:
        return "N/A"
    return "N/A"

def get_cpu_usage_from_dumpsys() -> Union[int,str]:
    """
    Use `dumpsys cpuinfo` as fallback. We attempt to extract a coarse usage estimate:
    dumpsys lines may include 'Load: 0.12 / 0.10 / 0.08' or per-process `%cpu`.
    We'll parse overall load1m and attempt to convert load to percentage heuristic:
      percent ≈ min(100, round((load1m / cores) * 100))
    """
    try:
        out = subprocess.check_output(["dumpsys", "cpuinfo"], stderr=subprocess.DEVNULL).decode(errors="ignore")
        # attempt to find 'Load:' line
        for line in out.splitlines():
            low = line.lower()
            if low.strip().startswith("load"):
                # example: "Load: 1.05 / 0.72 / 0.56"
                try:
                    loads = line.split(":",1)[1].strip().split("/")
                    one_min = float(loads[0].strip())
                    # detect core count using os.cpu_count() fallback
                    cores = os.cpu_count() or 1
                    percent = min(100, round((one_min / cores) * 100))
                    return percent
                except Exception:
                    continue
        # else, try to extract a combined percent by scanning for lines like '123%cpu'
        for line in out.splitlines():
            if "%cpu" in line.lower():
                val = parse_top_cpu_line(line)
                if val is not None:
                    return val
    except Exception:
        return "N/A"
    return "N/A"

async def get_best_cpu() -> Union[int,str]:
    """
    Return the most reliable CPU percentage we can get:
    1) try get_cpu_usage_from_top()
    2) try get_cpu_usage_from_dumpsys()
    3) return 'N/A'
    """
    top_val = await asyncio.to_thread(get_cpu_usage_from_top)
    if isinstance(top_val, int) and 0 <= top_val <= 100:
        return top_val
    ds_val = await asyncio.to_thread(get_cpu_usage_from_dumpsys)
    if isinstance(ds_val, int) and 0 <= ds_val <= 100:
        return ds_val
    return "N/A"

async def sample_cpu(n: int = 7, interval: float = 0.35) -> List[Union[int,str]]:
    """Sample CPU n times (non-blocking) and return list."""
    samples = []
    for _ in range(n):
        v = await get_best_cpu()
        samples.append(v)
        await asyncio.sleep(interval)
    return samples

# -----------------------
# Load chart (Option C)
# -----------------------
def samples_to_chart(samples: List[Union[int,str]]) -> Tuple[str,str]:
    """
    Returns numeric_line and bar_line.
    Numeric: "4% → 8% → 12%"
    Bars: "▁▂▅▄▆█"
    """
    blocks = ["▁","▂","▃","▄","▅","▆","▇","█"]
    numeric_parts = []
    bars = []
    for s in samples:
        if isinstance(s, int):
            numeric_parts.append(f"{s}%")
            idx = min(len(blocks)-1, max(0, (s * (len(blocks)-1)) // 100))
            bars.append(blocks[idx])
        else:
            numeric_parts.append("N/A")
            bars.append("·")
    numeric_line = " → ".join(numeric_parts)
    bar_line = "".join(bars)
    return numeric_line, bar_line

# -----------------------
# Stress test (Option B: system-level processes)
# -----------------------
async def stress_test_systemlevel(duration: float = 5.0, max_workers: int = None) -> Union[int,str]:
    """
    Spawn multiple native 'yes' worker processes (one per core, capped) and optionally an openssl speed process.
    Sample CPU while they run and then terminate them cleanly.
    Returns peak observed CPU percent (best-effort).
    """
    workers = max_workers or (os.cpu_count() or 4)
    # cap to avoid overwhelming device (8 is reasonable for 8 cores)
    workers = min(workers, 8)

    procs = []
    peak_samples = []

    # helper to spawn 'yes' processes
    def spawn_yes():
        try:
            p = subprocess.Popen(["yes"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return p
        except Exception:
            return None

    # helper to spawn openssl if available (heavier)
    def spawn_openssl():
        try:
            # openssl may not be present; this runs a continuous speed test until killed
            p = subprocess.Popen(["openssl", "speed", "aes-256-cbc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return p
        except Exception:
            return None

    # Spawn yes workers
    for _ in range(workers):
        p = spawn_yes()
        if p:
            procs.append(p)

    # Spawn openssl worker if available for extra load
    openssl_proc = spawn_openssl()
    if openssl_proc:
        procs.append(openssl_proc)

    # If no subprocess could be spawned, fallback to Python busy loop
    used_fallback = False
    if not procs:
        used_fallback = True
        # run a CPU-bound Python busy loop in thread
        def busy_loop(end_ts):
            x = 0
            while time.time() < end_ts:
                for _ in range(2000):
                    x += (_ ^ (x << 1)) & 0xFFFFFFFF
            return x
        thread_task = asyncio.to_thread(busy_loop, time.time() + duration)

    # Sample CPU while processes run
    end_ts = time.time() + duration
    try:
        while time.time() < end_ts:
            v = await get_best_cpu()
            peak_samples.append(v if isinstance(v, int) else 0)
            await asyncio.sleep(0.25)
    finally:
        # Clean up any spawned processes
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        # give short grace period
        await asyncio.sleep(0.4)
        for p in procs:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass
        # ensure fallback thread completes
        if used_fallback:
            try:
                await thread_task
            except Exception:
                pass

    # derive peak
    if peak_samples:
        peak = max(peak_samples)
        return peak
    return "N/A"

# -----------------------
# RAM & process memory
# -----------------------
def read_meminfo() -> Tuple[Union[int,str], Union[int,str]]:
    """
    Read /proc/meminfo and compute used & total (MB).
    Used = MemTotal - (MemFree + Buffers + Cached)
    """
    try:
        meminfo = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    val = int(parts[1])
                    meminfo[key] = val
        total_kb = meminfo.get("MemTotal", 0)
        free_kb = meminfo.get("MemFree", 0)
        buffers_kb = meminfo.get("Buffers", 0)
        cached_kb = meminfo.get("Cached", 0) + meminfo.get("SReclaimable", 0)  # include reclaimable
        used_kb = total_kb - (free_kb + buffers_kb + cached_kb)
        return (used_kb // 1024, total_kb // 1024)  # MB
    except Exception:
        # fallback via psutil if available
        if psutil:
            try:
                vm = psutil.virtual_memory()
                return (vm.used // (1024*1024), vm.total // (1024*1024))
            except Exception:
                return "N/A","N/A"
        return "N/A","N/A"

def get_process_rss_mb() -> Union[int,str]:
    """Read /proc/self/status VmRSS or use psutil Process()."""
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        kb = int(parts[1])
                        return kb // 1024
    except Exception:
        pass
    if psutil:
        try:
            p = psutil.Process()
            return p.memory_info().rss // (1024*1024)
        except Exception:
            return "N/A"
    return "N/A"

# -----------------------
# Storage helpers
# -----------------------
def get_storage_info(path: str) -> Tuple[Union[int,str], Union[int,str], Union[float,str]]:
    """
    Return used_MB, total_MB, percent_used for given path.
    """
    try:
        st = os.statvfs(path)
        total = (st.f_blocks * st.f_frsize) // (1024*1024)
        free = (st.f_bavail * st.f_frsize) // (1024*1024)
        used = total - free
        pct = round((used / total) * 100, 1) if total > 0 else "N/A"
        return used, total, pct
    except Exception:
        try:
            du = shutil.disk_usage(path)
            total = du.total // (1024*1024)
            free = du.free // (1024*1024)
            used = total - free
            pct = round((used / total) * 100, 1) if total > 0 else "N/A"
            return used, total, pct
        except Exception:
            return "N/A","N/A","N/A"

# -----------------------
# Network speed tests
# -----------------------
async def download_speed_test(url: str = "https://speed.hetzner.de/1MB.bin", max_bytes: int = 1_500_000, timeout: int = 12) -> Tuple[Union[float,str], Union[int,str]]:
    """
    Attempt to download ~1.5MB up to max_bytes and measure MB/s.
    Prefer requests. Return (MB/s, bytes_downloaded) or ("N/A","N/A")
    """
    if requests is None:
        # try speedtest module
        if speedtest:
            try:
                st = speedtest.Speedtest()
                down_bps = await asyncio.to_thread(st.download)
                return round((down_bps / 8) / (1024*1024),2), "approx"
            except Exception:
                return "N/A","N/A"
        return "N/A","N/A"
    try:
        t0 = time.time()
        with requests.get(url, stream=True, timeout=timeout) as r:
            total = 0
            for chunk in r.iter_content(chunk_size=32768):
                if not chunk:
                    break
                total += len(chunk)
                if total >= max_bytes:
                    break
        t1 = time.time()
        elapsed = max(0.0001, t1 - t0)
        speed_mb_s = round((total / (1024*1024)) / elapsed, 2)
        return speed_mb_s, total
    except Exception:
        # fallback to alternate url (Cloudflare)
        if requests:
            try:
                alt = "https://speed.cloudflare.com/__down?bytes=1000000"
                t0 = time.time()
                with requests.get(alt, stream=True, timeout=timeout) as r:
                    total = 0
                    for chunk in r.iter_content(32768):
                        if not chunk:
                            break
                        total += len(chunk)
                        if total >= max_bytes:
                            break
                t1 = time.time()
                elapsed = max(0.0001, t1 - t0)
                speed_mb_s = round((total / (1024*1024)) / elapsed, 2)
                return speed_mb_s, total
            except Exception:
                return "N/A","N/A"
        return "N/A","N/A"

async def upload_speed_test(upload_url: str = "https://0x0.st", payload_size: int = 700_000, timeout: int = 18) -> Tuple[Union[float,str], Union[int,str]]:
    """
    Upload random bytes to a simple paste service & measure MB/s.
    """
    if requests is None:
        return "N/A","N/A"
    try:
        payload = os.urandom(payload_size)
        t0 = time.time()
        r = requests.post(upload_url, files={"file":("speed.bin", payload)}, timeout=timeout)
        t1 = time.time()
        if r.status_code not in (200,201):
            return "N/A","N/A"
        elapsed = max(0.0001, t1 - t0)
        speed_mb_s = round((len(payload) / (1024*1024)) / elapsed, 2)
        return speed_mb_s, len(payload)
    except Exception:
        return "N/A","N/A"

# -----------------------
# Main /stats handler (loading animation)
# -----------------------
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Loading animation: multiple edits:
      1) Collecting...
      2) Sampling CPU...
      3) Stress test...
      4) Network...
      5) Final report
    """
    # initial message
    try:
        msg = await update.message.reply_text("⏳ *Collecting system info…*", parse_mode="Markdown")
    except Exception:
        # fallback if reply_text fails
        msg = await update.message.reply_text("Collecting system info...")

    # --- Uptime & basic memory (fast) ---
    uptime = format_uptime(time.time() - BOT_START)
    mem_used_mb, mem_total_mb = await asyncio.to_thread(read_meminfo)
    bot_ram = await asyncio.to_thread(get_process_rss_mb)

    # edit - sampling stage
    try:
        await msg.edit_text("🔍 *Sampling CPU (quick)*…", parse_mode="Markdown")
    except Exception:
        pass

    # CPU sampling
    cpu_samples = await sample_cpu(n=7, interval=0.35)
    numeric_line, bar_line = samples_to_chart(cpu_samples)
    baseline_cpu = cpu_samples[-1] if cpu_samples else "N/A"

    # edit - stress stage
    try:
        await msg.edit_text("🔥 *Running system-level stress-test (5s)…*", parse_mode="Markdown")
    except Exception:
        pass

    # run the new system-level stress-test (Option B)
    stress_peak = await stress_test_systemlevel(duration=5.0, max_workers=None)

    # edit - network stage
    try:
        await msg.edit_text("🌐 *Testing network speeds (download/upload)*…", parse_mode="Markdown")
    except Exception:
        pass

    # kick off network tasks concurrently
    dl_task = asyncio.create_task(download_speed_test())
    ul_task = asyncio.create_task(upload_speed_test())

    # Storage checks (fast)
    termux_path_candidates = [
        "/data/data/com.termux/files/usr",
        "/data/data/com.termux/files",
        os.path.expanduser("~")
    ]
    termux_path = next((p for p in termux_path_candidates if os.path.exists(p)), termux_path_candidates[-1])
    termux_used, termux_total, termux_pct = await asyncio.to_thread(get_storage_info, termux_path)

    phone_candidates = ["/sdcard", "/storage/emulated/0", "/storage/self/primary", "/"]
    phone_path = next((p for p in phone_candidates if os.path.exists(p)), "/")
    phone_used, phone_total, phone_pct = await asyncio.to_thread(get_storage_info, phone_path)

    # wait for network tasks (with timeout)
    try:
        dl_speed, dl_bytes = await asyncio.wait_for(dl_task, timeout=18)
    except Exception:
        dl_speed, dl_bytes = "N/A", "N/A"
    try:
        ul_speed, ul_bytes = await asyncio.wait_for(ul_task, timeout=20)
    except Exception:
        ul_speed, ul_bytes = "N/A", "N/A"

    # Final assembly of message (Markdown)
    final = (
        "**📊 System Stats**\n\n"
        f"⏱ **Uptime:** `{uptime}`\n\n"
        f"💾 **RAM:** `{mem_used_mb} MB / {mem_total_mb} MB`\n"
        f"🧠 **Bot RAM:** `{bot_ram} MB`\n\n"

        f"💽 **Termux Storage ({termux_path}):** `{termux_used} MB / {termux_total} MB` ({termux_pct}%)\n"
        f"📱 **Phone Storage ({phone_path}):** `{phone_used} MB / {phone_total} MB` ({phone_pct}%)\n\n"

        f"🔸 **CPU Baseline:** `{baseline_cpu}%`\n"
        f"🔸 **CPU Samples:** `{numeric_line}`\n"
        f"🔸 **Load Chart:** `{bar_line}`\n"
        f"🔸 **Stress-Test Peak:** `{stress_peak}%`\n\n"

        f"🌐 **Download Speed:** `{dl_speed} MB/s` `{dl_bytes}`\n"
        f"🌐 **Upload Speed:** `{ul_speed} MB/s` `{ul_bytes}`\n\n"

        "_Tip:_ If CPU stays flat even during stress-test, your device may keep cores in deep idle or cap background workloads. Running this system-level test uses native processes (yes/openssl) which should cause an observable spike. The test is short and cleaned up automatically."
    )

    try:
        await msg.edit_text(final, parse_mode="Markdown")
    except Exception:
        # final fallback plain text
        await msg.edit_text(final)

stats_command = CommandHandler("stats", stats_handler)
