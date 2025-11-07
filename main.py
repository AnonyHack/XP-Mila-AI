import logging
import threading
import asyncio
import signal
import time
from pyrogram import Client
from pyrogram.errors import FloodWait
from config import API_ID, API_HASH, BOT_TOKEN
from utils.keep_alive import start_keep_alive
from utils.startup import send_restart_notification, cleanup_bot_state
from utils.reminder_system import initialize_reminder_system, shutdown_reminder_system

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create Pyrogram Client
app = Client(
    "MilaAIBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="XPTOOLS")  # Load handlers from handlers/ and submodules
)

async def main():
    logger.info("🚀 Starting MILA AI Bot...")
    try:
        # Start keep-alive (including health server) in a separate thread
        keep_alive_thread = threading.Thread(target=start_keep_alive, daemon=True)
        keep_alive_thread.start()
        
        # Start the bot
        await app.start()
        logger.info("✅ Bot started successfully")
        
        # Send restart notification (automatically detects if it's a restart)
        await send_restart_notification(app)
        
        # Initialize reminder system
        await initialize_reminder_system(app)
        logger.info("⏰ Reminder system initialized")
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise
    finally:
        # Cleanup when bot stops
        logger.info("🛑 Bot is shutting down...")
        await shutdown_reminder_system()
        cleanup_bot_state()
        logger.info("✅ Bot shutdown complete")


if __name__ == "__main__":
    # Run the bot with FloodWait handling
    while True:
        try:
            app.run(main())
        except FloodWait as e:
            wait_time = int(e.value)
            logger.warning(f"⚠️ FloodWait: Telegram requires a wait of {wait_time} seconds. Sleeping...")
            time.sleep(wait_time)
            logger.info("⏳ Wait over, restarting bot...")
            continue
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break
