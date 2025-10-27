import os
import json
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from start import start_handler, button_handler as start_button_handler
from help import help_handler, button_handler as help_button_handler

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load or create JSON files
def load_json_files():
    json_files = ['links.json', 'files.json', 'admins.json', 'users.json']
    for file in json_files:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                if file == 'admins.json':
                    json.dump([], f)  # Empty list for admins
                elif file == 'users.json':
                    json.dump([], f)  # Empty list for users
                else:
                    json.dump({}, f)  # Empty dict for links and files

def main():
    # Load JSON files
    load_json_files()
    
    # Get bot token from environment variable
    load_dotenv("Bot_Token.env")
    TOKEN = os.getenv('BOT_TOKEN')
    if not TOKEN:
        print("Please set BOT_TOKEN environment variable")
        return
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CallbackQueryHandler(start_button_handler, pattern="^start_"))
    application.add_handler(CallbackQueryHandler(help_button_handler, pattern="^help_"))
    
    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
