import os
import sys
import json
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

OWNER_ID = 5373577888  # Your owner ID


# ✅ Check if the user is owner
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# 🔁 Restart Command
async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the bot safely (Owner only)."""
    user = update.effective_user
    user_id = user.id

    # Authorization check
    if not is_owner(user_id):
        await update.message.reply_text("🚫 You are not authorized to restart the bot.")
        return

    try:
        await update.message.delete()
    except Exception as e:
        print(f"⚠️ Could not delete restart command message: {e}")

    # Notify restart
    status_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="♻️ ʀᴇsᴛᴀʀᴛɪɴɢ ʙᴏᴛ...."
    )

    # Save restart info before restarting
    restart_info = {
        "chat_id": update.effective_chat.id,
        "user_id": user_id,
        "username": user.username or None,
        "first_name": user.first_name,
        "time": datetime.utcnow().isoformat()
    }

    with open("restart_info.json", "w") as f:
        json.dump(restart_info, f, indent=4)

    await asyncio.sleep(2)
    await status_msg.edit_text("🤖 ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ ")

    # Actual restart
    os.execl(sys.executable, sys.executable, *sys.argv)
