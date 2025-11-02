# admins.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from shared_functions import load_admins

OWNER_ID = 5373577888  # Your owner ID

async def admins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all bot admins including owner."""
    user_id = update.effective_user.id
    admins_data = load_admins()  # can be list or dict
    
    # Support both list & dict formats
    if isinstance(admins_data, dict):
        admins = admins_data.get("admins", [])
    else:
        admins = admins_data

    # Authorization check
    if user_id not in admins and user_id != OWNER_ID:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    admin_list = []

    # Add Owner first
    try:
        owner_user = await context.bot.get_chat(OWNER_ID)
        owner_name = escape_markdown(owner_user.first_name or "Private User", version=2)
        owner_mention = f"[{owner_name}](tg://user?id={OWNER_ID})"
        admin_list.append(f"👑 *Owner:* {owner_mention} \\(ID: `{OWNER_ID}`\\)")
    except Exception:
        admin_list.append(f"👑 *Owner:* Private User \\(ID: `{OWNER_ID}`\\)")

    # Add other admins
    for admin_id in admins:
        if admin_id == OWNER_ID:
            continue

        try:
            admin_user = await context.bot.get_chat(admin_id)
            admin_name = escape_markdown(admin_user.first_name or "Private User", version=2)
            admin_mention = f"[{admin_name}](tg://user?id={admin_id})"
            admin_list.append(f"⚡ *Admin:* {admin_mention} \\(ID: `{admin_id}`\\)")
        except Exception:
            admin_list.append(f"⚡ *Admin:* Private User \\(ID: `{admin_id}`\\)")

    admin_text = "\n".join(admin_list)

    message_text = (
        f"🛡️ *Administrators*\n\n"
        f"{admin_text}\n\n"
        f"📊 *Total Admins:* `{len(admins)}`"
    )

    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="admins_refresh")],
            [InlineKeyboardButton("❌ Close", callback_data="admins_close")]
        ]),
        parse_mode="MarkdownV2"
    )
    
async def admins_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "admins_refresh":
        await admins_handler(update, context)
        await query.message.delete()
    elif data == "admins_close":
        await query.message.delete()
