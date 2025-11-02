# middleware.py
from telegram import Update
from telegram.ext import ContextTypes

# Import your functions from other modules
from ban import is_banned
from users import auto_add_user

async def user_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Middleware that runs for every message:
    - Checks if the user is banned (stops execution if yes)
    - Adds new users automatically
    """
    # Only process messages (not callback queries, etc.)
    if not update.message:
        return
    
    # Auto-add new user to users.json
    await auto_add_user(update, context)

    # Check if the user is banned
    if await is_banned(update, context):
        return True  # stop further command execution
    
    return False  # continue with command execution
