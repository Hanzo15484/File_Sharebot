async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update the bot from GitHub."""
    try:
        await update.message.delete()
    except Exception as e:
        print(f"Could not delete message: {e}")
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    status_msg = await context.bot.send_message(
          chat_id=update.effective_chat.id,
          text="𖡡 ᴩᴜʟʟɪɴɢ ʟᴀᴛᴇꜱᴛ ᴜᴩᴅᴀᴛᴇ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ..."
      )
    
    try:
        # Pull latest changes from GitHub
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        
        if result.returncode == 0:
            changes = result.stdout.strip()
            if not changes or "Already up to date" in changes:
                await status_msg.edit_text("✅ ʙᴏᴛ ɪꜱ ᴀʟʀᴇᴀᴅy ᴜᴩ ᴛᴏ ᴅᴀᴛᴇ!")
                return
            
            await status_msg.edit_text(f"✅ ᴜᴩᴅᴀᴛᴇᴅ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ!\n\nChanges:\n{changes}")
            await asyncio.sleep(2)
            
            await status_msg.edit_text("♻️ ʀᴇꜱᴛᴀʀᴛɪɴɢ....")
            await asyncio.sleep(2)
            
            await status_msg.edit_text("✦ ʀᴇꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟy!")
            await asyncio.sleep(3)
            
            # Restart the bot
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            await status_msg.edit_text(f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴜᴩᴅᴀᴛᴇ: {result.stderr}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ ᴇʀʀᴏʀ ᴜᴩᴅᴀᴛɪɴɢ: {str(e)}")
