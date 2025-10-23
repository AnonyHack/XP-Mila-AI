import logging
import threading
import asyncio
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, PORT
from utils.keep_alive import start_keep_alive
from handlers import admin_commands

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create Pyrogram Client
app = Client(
    "WORMAIBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="handlers")
)

async def main():
    logger.info("🚀 Starting MILA AI Bot...")
    try:
        # Start keep-alive (including health server) in a separate thread
        logger.info(f"📡 Starting health server on port {PORT}")
        keep_alive_thread = threading.Thread(target=start_keep_alive, daemon=True)
        keep_alive_thread.start()
        
        # Start the bot
        await app.start()
        logger.info("✅ Bot started successfully")
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    app.run(main())
