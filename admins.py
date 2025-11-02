# admins.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from shared_functions import load_admins

async def admins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    admin_list = []
    
    # Add owner first
    try:
        owner_user = await context.bot.get_chat(5373577888)
        owner_mention = owner_user.mention_html()
        admin_list.append(f"👑 Owner: {owner_mention} (ID: `5373577888`)")
    except:
        admin_list.append(f"👑 Owner: Unknown (ID: `5373577888`)")
    
    # Add other admins
    for admin_id in admins:
        if admin_id == 5373577888:  # Skip owner as already added
            continue
            
        try:
            admin_user = await context.bot.get_chat(admin_id)
            admin_mention = admin_user.mention_html()
            admin_list.append(f"⚡ Admin: {admin_mention} (ID: `{admin_id}`)")
        except:
            admin_list.append(f"⚡ Admin: Unknown (ID: `{admin_id}`)")
    
    admin_text = "\n".join(admin_list)
    
    message_text = (
        f"🛡️ **Administrators**\n\n"
        f"{admin_text}\n\n"
        f"📊 **Total Admins:** `{len(admins)}`"  # +1 for owner
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
