from telegram import Update
from telegram.ext import ContextTypes

# Import your functions from other modules
from bans import is_banned
from users import auto_add_user

async def user_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Middleware that runs for every message:
    - Checks if the user is banned (stops execution if yes)
    - Adds new users automatically
    """
    # Check if the user is banned
    if await is_banned(update, context):
        return  # stop further command execution

    # Auto-add new user to users.json
    await auto_add_user(update, context)
