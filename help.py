import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Load admin data
def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return []

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 123456789:  # Replace with owner ID
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    help_text = (
        "Available Commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/genlink - Generate link\n"
        "/batchlink - Generate batch links\n"
        "/custombatch - Custom batch processing\n"
        "/fsub - Force subscribe\n"
        "/settings - Bot settings\n"
        "/promote - Promote user to admin\n"
        "/demote - Demote admin\n"
        "/ban - Ban user\n"
        "/unban - Unban user\n"
        "/users - Show users\n"
        "/admins - Show admins\n"
        "/update - Update bot\n"
        "/restart - Restart bot"
    )
    
    keyboard = [
        [InlineKeyboardButton("Back", callback_data="help_back")],
        [InlineKeyboardButton("Close", callback_data="help_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "help_back":
        # Go back to start menu
        user = query.from_user
        mention = user.mention_html()
        
        keyboard = [
            [InlineKeyboardButton("About", callback_data="start_about")],
            [InlineKeyboardButton("Help", callback_data="start_help")],
            [InlineKeyboardButton("Close", callback_data="start_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            with open('img.jpg', 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo,
                    caption=f"Hi {mention} welcome to File Store Bot",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            await query.message.delete()
        except FileNotFoundError:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Hi {mention} welcome to File Store Bot",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            await query.message.delete()
    
    elif data == "help_close":
        await query.message.delete()
