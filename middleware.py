# decorators.py
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from shared_functions import is_user_banned, auto_add_user

def check_ban_and_register(func):
    """
    Decorator that:
    1. Automatically adds users to users.json
    2. Checks if user is banned before executing any command
    3. If banned, sends ban message and stops execution
    4. If not banned, continues with the original command
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Only process if it's a message (not callback queries, etc.)
        if not update.message:
            return await func(update, context, *args, **kwargs)
        
        user_id = update.effective_user.id
        user = update.effective_user
        
        # 1. Auto-add user to users.json
        auto_add_user(user_id, user.username, user.first_name, user.last_name)
        
        # 2. Check if user is banned
        if is_user_banned(user_id):
            await update.message.reply_text(
                "🚫 **You have been banned from using this bot!**\n\n"
                "If you think this is a mistake, please contact the administrator.",
                parse_mode="Markdown"
            )
            return  # Stop execution here
        
        # 3. If not banned, continue with the original function
        return await func(update, context, *args, **kwargs)
    
    return wrapper
