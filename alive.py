import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

# Leave this EMPTY for now.
# You will replace it later using /settings command.
ALIVE_IMAGE_PATH = ""   # example: "assets/alive.jpg"


async def alive_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    caption = (
        "<b>💫 Bot Status: Alive & Running</b>\n\n"
        "Everything looks good, sweetheart.\n"
        "Your bot is active and responding smoothly. 💖"
    )

    # If image path is not added yet, send text only:
    if not ALIVE_IMAGE_PATH or not os.path.exists(ALIVE_IMAGE_PATH):
        await update.message.reply_text(caption, parse_mode="HTML")
        return

    # If image exists, send image + caption
    try:
        await update.message.reply_photo(
            photo=open(ALIVE_IMAGE_PATH, "rb"),
            caption=caption,
            parse_mode="HTML"
        )
    except Exception:
        # fallback to text if sending image fails
        await update.message.reply_text(caption, parse_mode="HTML")


alive_command = CommandHandler("alive", alive_handler)
