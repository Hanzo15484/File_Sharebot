# shared_functions.py
import json
import base64
import os

# Load admin data
def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return [5373577888]

# Load settings
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "start_image": "img.jpg",
            "help_image": "",
            "force_sub_image": "",
            "start_text": "Hi {mention} welcome to File Store Bot",
            "help_text": "Available Commands:\n\n/start - Start the bot\n/help - Show this help message\n/genlink - Generate link\n/batchlink - Generate batch links\n/custombatch - Custom batch processing\n/fsub - Force subscribe\n/settings - Bot settings\n/promote - Promote user to admin\n/demote - Demote admin\n/ban - Ban user\n/unban - Unban user\n/users - Show users\n/admins - Show admins\n/update - Update bot\n/restart - Restart bot",
            "auto_delete_time": 10,
            "protect_content": False
        }

# Load links data
def load_links():
    try:
        with open('links.json', 'r') as f:
            return json.load(f)
    except:
        return {}

# Save links data
def save_links(links):
    with open('links.json', 'w') as f:
        json.dump(links, f)

# Load force sub channels
def load_force_sub():
    try:
        with open('force_sub.json', 'r') as f:
            return json.load(f)
    except:
        return []

# Save force sub channels
def save_force_sub(channels):
    with open('force_sub.json', 'w') as f:
        json.dump(channels, f, indent=4)

# Encode file ID to base64
def encode_file_id(file_id):
    encoded = base64.urlsafe_b64encode(file_id.encode()).decode()
    return encoded.rstrip('=')

# Decode base64 to file ID
def decode_file_id(encoded_id):
    padding = 4 - (len(encoded_id) % 4)
    if padding != 4:
        encoded_id += '=' * padding
    try:
        return base64.urlsafe_b64decode(encoded_id.encode()).decode()
    except:
        return None
