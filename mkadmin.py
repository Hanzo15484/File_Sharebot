# mkadmin.py

import os
import json
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler, filters
import asyncio 
OWNER_ID = 5373577888

ADMINS_FILE = "admins.json"
LOG_FILE = "admin_logs.txt"
NOTIFIED_FILE = "expiry_notified.json"

# uid → {"24h": job, "12h": job, ..., "final": job}
SCHEDULED_JOBS = {}

# ============================================================
# FILE I/O HELPERS
# ============================================================

def load_admins_full():
    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("admins", [OWNER_ID])
            data.setdefault("expiry", {})
            return data
    except:
        return {"admins": [OWNER_ID], "expiry": {}}

def save_admins_full(data):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_notified():
    try:
        with open(NOTIFIED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_notified(data):
    with open(NOTIFIED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def log_action(text):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()} UTC • {text}\n")
    except:
        pass

# ============================================================
# TIME HELPERS (IST)
# ============================================================

def utcnow():
    return datetime.utcnow()

def to_ist(dt_utc):
    return dt_utc + timedelta(hours=5, minutes=30)

def format_ist(dt_utc):
    return to_ist(dt_utc).strftime("%d-%m-%Y %I:%M %p IST")

def format_ist_date(dt_utc):
    return to_ist(dt_utc).strftime("%d-%m-%Y")

def format_ist_time(dt_utc):
    return to_ist(dt_utc).strftime("%I:%M %p IST")


# ============================================================
# CANCEL JOBS
# ============================================================

def cancel_admin_jobs(application, user_id):
    if user_id not in SCHEDULED_JOBS:
        return
    for job in SCHEDULED_JOBS[user_id].values():
        try:
            job.schedule_removal()
        except:
            pass
    SCHEDULED_JOBS[user_id] = {}


# ============================================================
# SCHEDULE JOBS
# ============================================================

def schedule_admin_jobs(application, user_id, exp_dt_utc):
    cancel_admin_jobs(application, user_id)

    now = utcnow()
    remaining = (exp_dt_utc - now).total_seconds()
    if remaining <= 0:
        return

    SCHEDULED_JOBS[user_id] = {}
    jq = application.job_queue

    stages = [
        ("24h", 24 * 3600),
        ("12h", 12 * 3600),
        ("6h", 6 * 3600),
        ("2h", 2 * 3600),
    ]

    for label, sec_before in stages:
        t = exp_dt_utc - timedelta(seconds=sec_before)
        if t > now:
            job = jq.run_once(
                warning_callback,
                when=(t - now).total_seconds(),
                data={"uid": user_id, "label": label},
                name=f"warn_{user_id}_{label}"
            )
            SCHEDULED_JOBS[user_id][label] = job

    # final expiry job
    final_job = jq.run_once(
        expiry_callback,
        when=remaining,
        data={"uid": user_id},
        name=f"expire_{user_id}"
    )
    SCHEDULED_JOBS[user_id]["final"] = final_job


# ============================================================
# WARNING CALLBACK
# ============================================================

async def warning_callback(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    uid = job.data["uid"]
    label = job.data["label"]

    data = load_admins_full()
    expiry = data["expiry"]

    if str(uid) not in expiry:
        return

    exp_dt = datetime.fromisoformat(expiry[str(uid)])
    remain = (exp_dt - utcnow()).total_seconds()
    hrs = int(remain // 3600)
    mins = int((remain % 3600) // 60)

    try:
        await context.bot.send_message(
            chat_id=uid,
            text=(
                "⚠️ <b>Your admin access is expiring soon</b>\n\n"
                f"<b>Expires:</b> {format_ist(exp_dt)}\n"
                f"<b>Time left:</b> {hrs}h {mins}m"
            ),
            parse_mode="HTML"
        )
    except:
        pass

    log_action(f"WARNING {label} → {uid}")


# ============================================================
# FINAL EXPIRY CALLBACK
# ============================================================

async def expiry_callback(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    uid = job.data["uid"]

    data = load_admins_full()
    admins = data["admins"]
    expiry = data["expiry"]

    if uid in admins:
        admins.remove(uid)
    expiry.pop(str(uid), None)
    save_admins_full(data)

    cancel_admin_jobs(context.application, uid)

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Okay!", callback_data="expired_okay"),
            InlineKeyboardButton("Feedback", callback_data="expired_feedback"),
            InlineKeyboardButton("Owner", url="https://t.me/Quarel7")
        ]
    ])

    try:
        await context.bot.send_message(
            chat_id=uid,
            text=(
                "❌ <b>Your admin access has expired.</b>\n"
                "You no longer have admin privileges."
            ),
            parse_mode="HTML",
            reply_markup=kb
        )
    except:
        pass

    log_action(f"EXPIRED → {uid}")


# ============================================================
# FEEDBACK TEXT HANDLER
# ============================================================

async def feedback_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_feedback"):
        return

    context.user_data["awaiting_feedback"] = False
    user = update.effective_user
    msg = update.message.text

    # send feedback to owner
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                "📩 <b>Admin Feedback Received</b>\n\n"
                f"<b>From:</b> <a href=\"tg://user?id={user.id}\">{user.first_name}</a>\n"
                f"<b>User ID:</b> <code>{user.id}</code>\n\n"
                f"<b>Message:</b>\n{msg}"
            ),
            parse_mode="HTML"
        )
    except:
        pass

    # confirm to user
    await update.message.reply_html("✨ <b>Thanks for your feedback!</b>")


# ============================================================
# DURATION PARSER
# ============================================================

def parse_duration(s):
    if not s:
        return None
    s = s.lower().replace(" ", "")
    try:
        if s.endswith("min"):
            return timedelta(minutes=int(s[:-3]))
        if s.endswith("h"):
            return timedelta(hours=int(s[:-1]))
        if s.endswith("d"):
            return timedelta(days=int(s[:-1]))
        if s.endswith("y"):
            return timedelta(days=int(s[:-1]) * 365)
        if s.endswith("m"):
            return timedelta(days=int(s[:-1]) * 30)
    except:
        return None
    return None


# ============================================================
# PROMOTE
# ============================================================

async def promote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_admins_full()

    if user.id not in data["admins"] and user.id != OWNER_ID:
        return

    if len(context.args) == 0:
        await update.message.reply_html(
            "Use: <b>/promote &lt;user_id&gt; &lt;duration(optional)&gt;</b>\n\n"
            "Duration examples: 2d, 6h, 5min, 1y, 3m"
        )
        return

    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text("Invalid user ID.")
        return

    duration_str = context.args[1] if len(context.args) > 1 else None
    duration = parse_duration(duration_str)
    now = utcnow()

    admins = data["admins"]
    expiry = data["expiry"]

    # if already admin re-promote (reset timer)
    cancel_admin_jobs(context.application, target_id)

    if target_id not in admins:
        admins.append(target_id)

    if duration:
        exp_dt = now + duration
        expiry[str(target_id)] = exp_dt.isoformat()
        duration_text = format_ist(exp_dt)
    else:
        expiry.pop(str(target_id), None)
        exp_dt = None
        duration_text = "Permanent"

    save_admins_full(data)

    log_action(f"PROMOTED → {target_id} by {user.id} duration={duration_text}")

    # fetch user
    try:
        tg_user = await context.bot.get_chat(target_id)
        target_mention = tg_user.mention_html()
    except:
        target_mention = f'<a href="tg://user?id={target_id}">{target_id}</a>'

    promoter_mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

    msg = (
        "<b>Admin Promoted Successfully ✔</b>\n\n"
        f"<b>Name:</b> {target_mention}\n"
        f"<b>User ID:</b> <code>{target_id}</code>\n"
        f"<b>Promoted by:</b> {promoter_mention}\n"
        f"<b>Promoted on:</b> {format_ist(now)}\n"
        f"<b>Duration:</b> {duration_text}\n\n"
        "<b>Usage:</b>\n"
        "/promote &lt;user_id&gt; &lt;duration(optional)&gt;\n\n"
        "<b>Duration Format:</b>\n"
        "y=year, m=month, d=day, h=hour, min=minute\n"
        "<b>Examples:</b> 2d, 6h, 5min, 1y, 3m"
    )

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Owner", url="https://t.me/Quarel7"),
            InlineKeyboardButton("✖ Close", callback_data="close_msg"),
        ]
    ])

    await update.message.reply_html(msg, reply_markup=kb)

    # notify promoted user
    try:
        user_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 Owner", url="https://t.me/Quarel7")],
            [InlineKeyboardButton("Okay!", callback_data="admin_okay")]
        ])
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                "🎉 <b>Congratulations!</b>\n\n"
                "You are now an <b>admin</b>.\n"
                f"<b>Expires:</b> {duration_text}"
            ),
            parse_mode="HTML",
            reply_markup=user_kb
        )
    except:
        pass

    # schedule jobs
    if exp_dt:
        schedule_admin_jobs(context.application, target_id, exp_dt)


# ============================================================
# DEMOTE
# ============================================================

async def demote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_admins_full()

    if user.id not in data["admins"] and user.id != OWNER_ID:
        return

    if len(context.args) == 0:
        await update.message.reply_html("Use: <b>/demote &lt;user_id&gt;</b>")
        return

    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text("Invalid ID.")
        return

    admins = data["admins"]
    expiry = data["expiry"]

    if target_id not in admins:
        await update.message.reply_text("This user is not admin.")
        return

    if target_id == OWNER_ID:
        await update.message.reply_text("Cannot demote owner.")
        return

    admins.remove(target_id)
    expiry.pop(str(target_id), None)
    save_admins_full(data)
    cancel_admin_jobs(context.application, target_id)

    log_action(f"DEMOTED → {target_id} by {user.id}")

    # mention
    try:
        tg_user = await context.bot.get_chat(target_id)
        mention = tg_user.mention_html()
    except:
        mention = f'<a href="tg://user?id={target_id}">{target_id}</a>'

    msg = (
        "<b>User Demoted Successfully ✔</b>\n\n"
        f"<b>Name:</b> {mention}\n"
        f"<b>User ID:</b> <code>{target_id}</code>\n"
        f"<b>Demoted by:</b> <a href=\"tg://user?id={user.id}\">{user.first_name}</a>\n"
        f"<b>Demoted on:</b> {format_ist(utcnow())}"
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✖ Close", callback_data="close_msg")]
    ])

    await update.message.reply_html(msg, reply_markup=kb)

    # notify user
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="⚠️ Your admin role has been removed.",
        )
    except:
        pass


# ============================================================
# ADMIN PANEL + CALLBACKS
# ============================================================

def build_admin_panel_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 Admins", callback_data="panel_admins")],
        [InlineKeyboardButton("➕ Promote", callback_data="panel_promote")],
        [InlineKeyboardButton("➖ Demote", callback_data="panel_demote")],
        [InlineKeyboardButton("⚠ Expiring Admins", callback_data="panel_expiring")],
        [InlineKeyboardButton("📜 Logs", callback_data="panel_logs")],
        [InlineKeyboardButton("👑 Owner", url="https://t.me/Quarel7")],
        [InlineKeyboardButton("✖ Close Panel", callback_data="close_msg")]
    ])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_admins_full()
    if update.effective_user.id not in data["admins"] and update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_html(
        "<b>🛠 Admin Control Panel</b>",
        reply_markup=build_admin_panel_kb()
    )


# ------------------------------------------------------------
# Panel callback
# ------------------------------------------------------------

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    d = load_admins_full()
    admins = d["admins"]
    expiry = d["expiry"]

    # --------------------
    # ADMIN LIST
    # --------------------
    if data == "panel_admins":
        text = "<b>👑 Current Admins</b>\n\n"
        for uid in admins:
            try:
                u = await context.bot.get_chat(uid)
                mention = u.mention_html()
            except:
                mention = f'<a href="tg://user?id={uid}">{uid}</a>'
            if str(uid) in expiry:
                exp_dt = datetime.fromisoformat(expiry[str(uid)])
                e = format_ist(exp_dt)
            else:
                e = "Permanent"

            text += f"• {mention}\n  ID: <code>{uid}</code>\n  Expires: {e}\n\n"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅ Back", callback_data="admin_back"),
             InlineKeyboardButton("✖ Close", callback_data="close_msg")]
        ])

        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        return

    # --------------------
    # Promote info
    # --------------------
    if data == "panel_promote":
        await query.message.edit_text(
            "Use:\n<b>/promote &lt;user_id&gt; &lt;duration(optional)&gt;</b>\n"
            "Examples: 2d, 6h, 5min, 1y, 3m",
            parse_mode="HTML"
        )
        return

    # --------------------
    # Demote info
    # --------------------
    if data == "panel_demote":
        await query.message.edit_text(
            "Use:\n<b>/demote &lt;user_id&gt;</b>",
            parse_mode="HTML"
        )
        return

    # --------------------
    # Logs info
    # --------------------
    if data == "panel_logs":
        await query.message.edit_text("Open logs:\n<b>/admin_logs</b>", parse_mode="HTML")
        return

    # --------------------
    # EXPIRING ADMINS
    # --------------------
    if data == "panel_expiring":
        now = utcnow()
        soon = []
        long = []

        for uid, ts in expiry.items():
            exp_dt = datetime.fromisoformat(ts)
            rem = (exp_dt - now).total_seconds()

            try:
                u = await context.bot.get_chat(int(uid))
                m = u.mention_html()
            except:
                m = f'<a href="tg://user?id={uid}">{uid}</a>'

            if rem <= 86400:
                h = int(rem // 3600)
                mn = int((rem % 3600) // 60)
                soon.append(f"• {m} — <b>{h}h {mn}m</b>")
            else:
                long.append(f"• {m} — Expires: {format_ist(exp_dt)}")

        text = ""
        if soon:
            text += "<b>⚠ Expiring Within 24h</b>\n\n" + "\n".join(soon) + "\n\n"
        if long:
            text += "<b>🕒 Long-term Admins</b>\n\n" + "\n".join(long)

        if not soon and not long:
            await query.message.edit_text("No admins with expiry.", parse_mode="HTML")
            return

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅ Back", callback_data="admin_back"),
             InlineKeyboardButton("✖ Close", callback_data="close_msg")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        return

    # --------------------
    # BACK BUTTON
    # --------------------
    if data == "admin_back":
        await query.message.edit_text(
            "<b>🛠 Admin Control Panel</b>",
            parse_mode="HTML",
            reply_markup=build_admin_panel_kb()
        )
        return

    # --------------------
    # Expiry: "Okay!"
    # --------------------
    if data == "expired_okay":
        await query.answer("Thank you! For using our bot please give us feedback to improve our bot", show_alert=True)
        await asyncio.sleep(10)
        await query.message.delete()
        return

    if data == "admin_okay":
        await query.answer("Congratulations 🎉 you have now access to our bot", show_alert=True)
        await asyncio.sleep(0.007)
        await query.message.delete()
        return
        
    # --------------------
    # Expiry: Feedback
    # --------------------
    if data == "expired_feedback":
        context.user_data["awaiting_feedback"] = True
        await query.message.reply_html("💬 <b>Please type your feedback.</b>")
        return

    # --------------------
    # Close
    # --------------------
    if data == "close_msg":
        try:
            await query.message.delete()
        except:
            pass
        return


# ============================================================
# LOG VIEWER (simplified)
# ============================================================

async def admin_logs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_admins_full()
    if user.id not in data["admins"] and user.id != OWNER_ID:
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except:
        lines = []

    if not lines:
        await update.message.reply_text("No logs.")
        return

    lines = lines[-40:]  # last 40 entries
    text = "<b>📜 Admin Logs</b>\n\n" + "".join(lines)
    await update.message.reply_html(text)


# ============================================================
# REGISTER HANDLERS
# ============================================================

def register_mkadmin_handlers(app):
    from telegram.ext import CommandHandler, CallbackQueryHandler

    app.add_handler(CommandHandler("promote", promote_handler))
    app.add_handler(CommandHandler("demote", demote_handler))
    app.add_handler(CommandHandler("admin_logs", admin_logs_handler))
    app.add_handler(CommandHandler("adminpanel", admin_panel))

    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^panel_"))
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^expired_.*"))
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^close_msg$"))

    # feedback messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_text_handler), 
    group=4)
