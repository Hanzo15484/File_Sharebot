# mkadmin.py
# COMPLETE ADMIN SYSTEM — FULLY MERGED AND OPTIMIZED

import os
import json
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler
)

OWNER_ID = 5373577888

# ============================================================
#               FULL ADMIN DATA HANDLING
# ============================================================

def load_admins_full():
    try:
        with open("admins.json", "r") as f:
            return json.load(f)
    except:
        return {"admins": [OWNER_ID], "expiry": {}}


def save_admins_full(data):
    with open("admins.json", "w") as f:
        json.dump(data, f, indent=4)


# ============================================================
#               EXPIRY NOTIFICATION STORAGE
# ============================================================

def load_notified():
    try:
        with open("expiry_notified.json", "r") as f:
            return json.load(f)
    except:
        return {}


def save_notified(data):
    with open("expiry_notified.json", "w") as f:
        json.dump(data, f, indent=4)


# ============================================================
#                     LOGGING + ROTATION
# ============================================================

def rotate_logs(max_size_kb=300):
    try:
        size = os.path.getsize("admin_logs.txt") / 1024
        if size > max_size_kb:
            with open("admin_logs.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()

            lines = lines[-250:]

            with open("admin_logs.txt", "w", encoding="utf-8") as f:
                f.writelines(lines)

            log_action("LOG ROTATION → Old logs removed")
    except:
        pass


def log_action(text):
    rotate_logs()
    with open("admin_logs.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()} UTC • {text}\n")


# ============================================================
#               AUTO-REMOVE EXPIRED ADMINS
# ============================================================

def cleanup_expired_admins():
    data = load_admins_full()
    admins = data["admins"]
    expiry = data.get("expiry", {})
    notified = load_notified()

    now = datetime.utcnow()
    expired_list = []
    changed = False

    for uid, exp_time in expiry.copy().items():
        exp_dt = datetime.fromisoformat(exp_time)
        if now >= exp_dt:
            expired_list.append(int(uid))

    for uid in expired_list:
        if uid in admins:
            admins.remove(uid)

        expiry.pop(str(uid), None)
        notified.pop(str(uid), None)

        log_action(f"AUTO-EXPIRE → Admin {uid} removed by system")
        changed = True

    if changed:
        data["admins"] = admins
        data["expiry"] = expiry
        save_admins_full(data)
        save_notified(notified)

    return expired_list


# ============================================================
#                EXPIRY NOTIFICATION SYSTEM
# ============================================================

async def notify_expiring_admins(context):
    data = load_admins_full()
    expiry = data["expiry"]
    notified = load_notified()
    now = datetime.utcnow()

    THRESHOLDS = {
        "24h": 24 * 3600,
        "12h": 12 * 3600,
        "6h": 6 * 3600,
        "2h": 2 * 3600,
    }

    for uid, exp_time in expiry.items():
        exp_dt = datetime.fromisoformat(exp_time)
        remaining = (exp_dt - now).total_seconds()

        # Timeout happened
        if remaining <= 0:
            if str(uid) not in notified or notified[str(uid)] != "timeout":
                try:
                    await context.bot.send_message(
                        int(uid),
                        "❌ Your admin access has expired.\nYou are no longer an admin.",
                        parse_mode="HTML"
                    )
                except:
                    pass

                notified[str(uid)] = "timeout"
                save_notified(notified)
            continue

        # Send notifications for thresholds
        for label, seconds in THRESHOLDS.items():
            if remaining <= seconds:

                if str(uid) in notified and notified[str(uid)] == label:
                    break  # Already notified this level

                hours = int(seconds / 3600)

                text = (
                    f"⚠️ <b>Admin Access Expiring Soon</b>\n\n"
                    f"<b>Remaining:</b> ~{hours} hours\n"
                    f"<b>Expires:</b> {exp_dt.strftime('%d-%m-%Y %I:%M %p UTC')}"
                )

                try:
                    await context.bot.send_message(int(uid), text, parse_mode="HTML")
                except:
                    pass

                notified[str(uid)] = label
                save_notified(notified)

                log_action(f"EXPIRY NOTICE ({label}) → {uid}")

                break


# ============================================================
#                      MENTION HELPER
# ============================================================

def mention_html(user_id, name):
    name = name.replace("<", "").replace(">", "")
    return f"<a href=\"tg://user?id={user_id}\">{name}</a>"


# ============================================================
#                      DURATION PARSER
# ============================================================

def parse_duration(duration_str):
    if not duration_str:
        return None

    try:
        if duration_str.endswith("d"):
            return timedelta(days=int(duration_str[:-1]))

        if duration_str.endswith("m"):
            return timedelta(days=int(duration_str[:-1]) * 30)

        if duration_str.endswith("y"):
            return timedelta(days=int(duration_str[:-1]) * 365)

        if duration_str.endswith("h"):
            return timedelta(hours=int(duration_str[:-1]))

        if duration_str.endswith("min"):
            return timedelta(minutes=int(duration_str[:-3]))
    except:
        return None

    return None


# ============================================================
#                         /PROMOTE
# ============================================================

async def promote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cleanup_expired_admins()
    await notify_expiring_admins(context)

    data = load_admins_full()
    admins = data["admins"]
    expiry_map = data["expiry"]

    issuer = update.effective_user

    if issuer.id not in admins and issuer.id != OWNER_ID:
        return

    if len(context.args) == 0:
        await update.message.reply_html(
            "ᴘʟᴇᴀsᴇ ᴜsᴇ <b>/promote &lt;user_id&gt; &lt;duration(optional)&gt;</b>"
        )
        return

    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_html("❌ Invalid user_id.")
        return

    duration_str = context.args[1] if len(context.args) > 1 else None
    duration = parse_duration(duration_str)

    if target_id in admins:
        await update.message.reply_html("⚠️ User is already an admin.")
        return

    admins.append(target_id)
    now_utc = datetime.utcnow()

    if duration:
        exp_at = now_utc + duration
        expiry_map[str(target_id)] = exp_at.isoformat()
        exp_text = exp_at.strftime("%d-%m-%Y %I:%M %p UTC")
    else:
        exp_text = "Permanent"
        expiry_map.pop(str(target_id), None)

    data["admins"] = admins
    data["expiry"] = expiry_map
    save_admins_full(data)

    try:
        t_user = await context.bot.get_chat(target_id)
        t_name = t_user.first_name
    except:
        t_name = "Unknown User"

    name_html = mention_html(target_id, t_name)
    promoted_by = mention_html(issuer.id, issuer.first_name)

    date = now_utc.strftime("%d-%m-%Y")
    time = now_utc.strftime("%I:%M %p")

    log_action(f"PROMOTED → {target_id} by {issuer.id} | Duration: {exp_text}")

    btn = InlineKeyboardMarkup([[InlineKeyboardButton("✖ Close", callback_data="close_msg")]])

    msg = (
        "<b>Admin Promoted Successfully ✔</b>\n\n"
        f"<b>Name:</b> {name_html}\n"
        f"<b>User ID:</b> <code>{target_id}</code>\n"
        f"<b>Promoted by:</b> {promoted_by}\n"
        f"<b>Promoted on:</b> {date} (UTC)\n"
        f"<b>Time:</b> {time} (UTC)\n"
        f"<b>Duration:</b> {exp_text}"
    )

    await update.message.reply_html(msg, reply_markup=btn)
    await notify_expiring_admins(context)


# ============================================================
#                          /DEMOTE
# ============================================================

async def demote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cleanup_expired_admins()
    await notify_expiring_admins(context)

    data = load_admins_full()
    admins = data["admins"]
    expiry_map = data["expiry"]

    issuer = update.effective_user

    if issuer.id not in admins and issuer.id != OWNER_ID:
        return

    if len(context.args) == 0:
        await update.message.reply_html("ᴘʟᴇᴀsᴇ ᴜsᴇ <b>/demote &lt;user_id&gt;</b>")
        return

    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_html("❌ Invalid user_id.")
        return

    if target_id not in admins:
        await update.message.reply_html("⚠️ This user is not an admin.")
        return

    if target_id == OWNER_ID:
        await update.message.reply_html("❌ You cannot demote the owner.")
        return

    admins.remove(target_id)
    expiry_map.pop(str(target_id), None)

    data["admins"] = admins
    data["expiry"] = expiry_map
    save_admins_full(data)

    try:
        t_user = await context.bot.get_chat(target_id)
        t_name = t_user.first_name
    except:
        t_name = "Unknown User"

    now_utc = datetime.utcnow()

    log_action(f"DEMOTED → {target_id} by {issuer.id}")

    name_html = mention_html(target_id, t_name)
    demoted_by = mention_html(issuer.id, issuer.first_name)

    date = now_utc.strftime("%d-%m-%Y")
    time = now_utc.strftime("%I:%M %p")

    btn = InlineKeyboardMarkup([[InlineKeyboardButton("✖ Close", callback_data="close_msg")]])

    msg = (
        "<b>User Demoted Successfully ✔</b>\n\n"
        f"<b>Name:</b> {name_html}\n"
        f"<b>User ID:</b> <code>{target_id}</code>\n"
        f"<b>Demoted by:</b> {demoted_by}\n"
        f"<b>Demoted on:</b> {date} (UTC)\n"
        f"<b>Time:</b> {time} (UTC)"
    )

    await update.message.reply_html(msg, reply_markup=btn)
    await notify_expiring_admins(context)


# ============================================================
#                    /ADMIN_LOGS (Pagination)
# ============================================================

async def admin_logs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cleanup_expired_admins()
    await notify_expiring_admins(context)

    data = load_admins_full()
    admins = data["admins"]

    if update.effective_user.id not in admins and update.effective_user.id != OWNER_ID:
        return

    page = int(context.args[0]) if context.args else 1

    try:
        with open("admin_logs.txt", "r", encoding="utf-8") as f:
            logs = f.readlines()
    except:
        logs = []

    logs.reverse()
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page

    chunk = logs[start:end]

    if not chunk:
        await update.message.reply_text("No logs available.")
        return

    text = "<b>📜 Admin Logs</b>\n\n"
    for line in chunk:
        text += f"• {line}\n"

    buttons = []

    if start > 0:
        buttons.append(InlineKeyboardButton("⬅ Prev", callback_data=f"log_prev_{page}"))

    if end < len(logs):
        buttons.append(InlineKeyboardButton("Next ➡", callback_data=f"log_next_{page}"))

    markup = InlineKeyboardMarkup([buttons]) if buttons else None

    await update.message.reply_html(text, reply_markup=markup)


async def logs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("log_prev_"):
        p = int(data.split("_")[-1]) - 1
    elif data.startswith("log_next_"):
        p = int(data.split("_")[-1]) + 1
    else:
        return

    await query.answer()
    await admin_logs_handler(update, context)


# ============================================================
#                   FULL ADMIN CONTROL PANEL
# ============================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cleanup_expired_admins()
    await notify_expiring_admins(context)

    data = load_admins_full()
    admins = data["admins"]

    if update.effective_user.id not in admins and update.effective_user.id != OWNER_ID:
        return

    kb = [
        [InlineKeyboardButton("👑 Admins", callback_data="panel_admins")],
        [InlineKeyboardButton("➕ Promote", callback_data="panel_promote")],
        [InlineKeyboardButton("➖ Demote", callback_data="panel_demote")],
        [InlineKeyboardButton("📜 Logs", callback_data="panel_logs")],
        [InlineKeyboardButton("⚠ Expiring Admins", callback_data="panel_expiring")],
        [InlineKeyboardButton("✖ Close Panel", callback_data="close_msg")],
    ]

    await update.message.reply_html(
        "<b>🛠 Admin Control Panel</b>\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(kb)
    )


async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # Show admins
    if data == "panel_admins":
        data2 = load_admins_full()
        adm = data2["admins"]
        txt = "<b>👑 Current Admins:</b>\n\n"
        for a in adm:
            txt += f"• <code>{a}</code>\n"
        await query.message.edit_text(txt, parse_mode="HTML")

    # Promote instructions
    elif data == "panel_promote":
        await query.message.edit_text(
            "Use:\n<b>/promote &lt;user_id&gt; &lt;duration(optional)&gt;</b>",
            parse_mode="HTML"
        )

    # Demote instructions
    elif data == "panel_demote":
        await query.message.edit_text(
            "Use:\n<b>/demote &lt;user_id&gt;</b>",
            parse_mode="HTML"
        )

    # View logs
    elif data == "panel_logs":
        await query.message.edit_text(
            "Open logs with:\n<b>/admin_logs</b>",
            parse_mode="HTML"
        )

    # Expiring admins (<24h)
    elif data == "panel_expiring":
        data2 = load_admins_full()
        expiry = data2["expiry"]
        now = datetime.utcnow()

        txt = "<b>⚠ Admins Expiring Soon:</b>\n\n"
        found = False

        for uid, exp in expiry.items():
            exp_dt = datetime.fromisoformat(exp)
            remaining = exp_dt - now

            if remaining.total_seconds() <= 86400:
                found = True
                txt += (
                    f"• <code>{uid}</code>\n"
                    f"  Expires: {exp_dt.strftime('%d-%m-%Y %I:%M %p UTC')}\n"
                    f"  Time Left: {str(remaining).split('.')[0]}\n\n"
                )

        if not found:
            txt = "No admins expiring within 24 hours."

        await query.message.edit_text(txt, parse_mode="HTML")

    await query.answer()


# ============================================================
#                CLOSE INLINE MESSAGE
# ============================================================

async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.message.delete()
    except:
        await update.callback_query.answer("Already removed.")


# ============================================================
#            REGISTER HANDLERS FOR main.py
# ============================================================

def register_mkadmin_handlers(application):
    application.add_handler(CommandHandler("promote", promote_handler))
    application.add_handler(CommandHandler("demote", demote_handler))
    application.add_handler(CommandHandler("admin_logs", admin_logs_handler))
    application.add_handler(CommandHandler("adminpanel", admin_panel))

    application.add_handler(CallbackQueryHandler(close_callback, pattern="close_msg"))
    application.add_handler(CallbackQueryHandler(logs_callback, pattern="log_"))
    application.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="panel_"))
