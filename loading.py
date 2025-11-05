import asyncio

async def show_loading_placeholder(target):
    """Show a short blank (or loading) placeholder before sending actual message."""
    try:
        # Works for both message and query
        if hasattr(target, "edit_message_text"):
            # For callback query (inline buttons)
            await target.edit_message_text("‎", parse_mode="Markdown")
        else:
            # For normal commands like /start, /help
            await target.reply_text("‎", parse_mode="Markdown")
        await asyncio.sleep(0.3)
    except Exception:
        pass
