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

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mention = user.mention_html()
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("About", callback_data="start_about")],
        [InlineKeyboardButton("Help", callback_data="start_help")],
        [InlineKeyboardButton("Close", callback_data="start_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with image
    try:
        with open('img.jpg', 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo,
                caption=f"Hi {mention} welcome to File Store Bot",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except FileNotFoundError:
        # If image not found, send text only
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Hi {mention} welcome to File Store Bot",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "start_about":
        about_text = (
            "Bot Name - File Store Bot\n"
            "Bot Username - @YourBotUsername\n"
            "Python Version - 3.8+\n"
            "Database - JSON\n"
            "Owner - Your Name\n\n"
            "This bot is only for Anime Fable"
        )
        
        keyboard = [
            [InlineKeyboardButton("Back", callback_data="start_back")],
            [InlineKeyboardButton("Close", callback_data="start_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption=about_text,
            reply_markup=reply_markup
        )
    
    elif data == "start_help":
        admins = load_admins()
        if user_id not in admins and user_id != 123456789:  # Replace with owner ID
            await query.answer("You are not my senpai!", show_alert=True)
            return
        
        # If user is admin/owner, show help
        keyboard = [
            [InlineKeyboardButton("Back", callback_data="start_back")],
            [InlineKeyboardButton("Close", callback_data="start_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption="Help section - Click Help button for detailed help",
            reply_markup=reply_markup
        )
    
    elif data == "start_back":
        user = query.from_user
        mention = user.mention_html()
        
        keyboard = [
            [InlineKeyboardButton("About", callback_data="start_about")],
            [InlineKeyboardButton("Help", callback_data="start_help")],
            [InlineKeyboardButton("Close", callback_data="start_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption=f"Hi {mention} welcome to File Store Bot",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif data == "start_close":
        await query.message.delete()
