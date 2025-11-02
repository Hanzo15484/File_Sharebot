import os
import sys
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from users import load_data, save_data  # make sure you import them properly
from admins import is_admin  # or your is_owner check

def is_owner(user_id):
    # You can define your own owner ID check
    return user_id == 5373577888  # replace with your Telegram ID

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the bot."""
    try:
        await update.message.delete()
    except Exception as e:
        print(f"Could not delete message: {e}")

    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    status_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="ʀᴇꜱᴛᴀʀᴛɪɴɢ ʙᴏᴛ..."
    )

    await asyncio.sleep(2)
    await status_msg.edit_text("ʙᴏᴛ ʀᴇꜱᴛᴀʀᴛᴇᴅ ✅")
    await asyncio.sleep(3)

    # ✅ Fixed — no `await` here
    data = load_data()
    data["restart"] = {
        "chat_id": update.effective_chat.id,
        "message_id": update.effective_message.message_id,
        "time": datetime.utcnow().isoformat()
    }
    save_data(data)

    # Restart
    os.execl(sys.executable, sys.executable, *sys.argv)
