import os
from dotenv import load_dotenv

load_dotenv()

# Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Payments
YUKASSA_TOKEN = os.getenv("YUKASSA_TOKEN")

# Admins
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(','))) if os.getenv("ADMIN_IDS") else []

# Private Channel
PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")

# Other settings (can be expanded later)
WORKFLOWS_DIR = os.path.join(os.getcwd(), 'workflows')
WATERMARKED_DIR = os.path.join(os.getcwd(), 'watermarked')
LOGS_DIR = os.path.join(os.getcwd(), 'logs')
BACKUPS_DIR = os.path.join(os.getcwd(), 'backups')
SCRIPTS_DIR = os.path.join(os.getcwd(), 'scripts')
