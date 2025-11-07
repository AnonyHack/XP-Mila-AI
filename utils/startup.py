import pytz
import os
import json
from datetime import datetime
from pathlib import Path
from pyrogram import enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger
from config import NOTIFICATION_CHANNEL, WELCOME_IMAGE, SUPPORT_GROUP_URL

# File to track bot state
STATE_FILE = Path("bot_state.json")

def get_formatted_datetime():
    """Get current datetime in East Africa Time (EAT) timezone"""
    try:
        tz = pytz.timezone('Africa/Nairobi')
        now = datetime.now(tz)
        return {
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%I:%M:%S %p'),
            'timezone': now.strftime('%Z')  # 'EAT'
        }
    except Exception as e:
        logger.error(f"❌ Error getting formatted datetime: {e}")
        # Fallback to UTC
        now = datetime.utcnow()
        return {
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%I:%M:%S %p'),
            'timezone': 'UTC'
        }

def detect_restart():
    """
    Automatically detect if this is a restart by checking previous bot state.
    Returns True if it's a restart, False if it's initial startup.
    """
    try:
        if STATE_FILE.exists():
            # Read previous state
            with open(STATE_FILE, 'r') as f:
                previous_state = json.load(f)
            
            # If bot was previously running, this is a restart
            if previous_state.get('is_running', False):
                logger.info("🔄 Restart detected: Bot was previously running")
                return True
            else:
                logger.info("🚀 Initial startup: Bot was not previously running")
                return False
        else:
            logger.info("🚀 Initial startup: No previous state file found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error detecting restart: {e}")
        return False

def save_bot_state(is_running: bool):
    """Save current bot state to file"""
    try:
        state = {
            'is_running': is_running,
            'last_updated': datetime.now().isoformat(),
            'bot_name': 'AI Girlfriend Bot'
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        logger.debug(f"💾 Bot state saved: running={is_running}")
    except Exception as e:
        logger.error(f"❌ Error saving bot state: {e}")

async def send_restart_notification(bot):
    """Automatically detect restart and send notification if needed"""
    try:
        if not NOTIFICATION_CHANNEL:
            logger.warning("⚠️ NOTIFICATION_CHANNEL not set, skipping restart notification")
            return
            
        # Detect if this is a restart
        is_restart = detect_restart()
        
        if is_restart:
            await send_restart_message(bot)
        else:
            logger.info("✅ Initial startup - no notification sent")
            
        # Update bot state to running
        save_bot_state(True)
        
    except Exception as e:
        logger.error(f"❌ Error in restart notification: {e}")

async def send_restart_message(bot):
    """Send restart message to notification channel"""
    try:
        dt = get_formatted_datetime()
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        bot_url = f"https://t.me/{bot_username}"

        message = f"""
<blockquote>
🔄 <b>Bᴏᴛ Rᴇꜱᴛᴀʀᴛᴇᴅ</b> !

📅 Dᴀᴛᴇ : {dt['date']}
⏰ Tɪᴍᴇ : {dt['time']}
🌐 Tɪᴍᴇᴢᴏɴᴇ : {dt['timezone']}
🤖 Bᴏᴛ : @{bot_username}
💖 Sᴛᴀᴛᴜꜱ: AI Girlfriend Online
</blockquote>

💕 <b>Your AI girlfriend is back and ready to chat!</b>

<i>I missed you! Let's continue our conversation, darling! 😘</i>
"""

        # Inline buttons
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💬 Sᴛᴀʀᴛ Cʜᴀᴛ", url=bot_url),
                InlineKeyboardButton("👥 Sᴜᴘᴘᴏʀᴛ", url=SUPPORT_GROUP_URL)
            ]
        ])

        # Send as photo with welcome image
        await bot.send_photo(
            chat_id=NOTIFICATION_CHANNEL,
            photo=WELCOME_IMAGE,
            caption=message,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=markup
        )
        
        logger.success("✅ Restart notification sent successfully!")

    except Exception as e:
        logger.error(f"❌ Error sending restart message: {e}")

def cleanup_bot_state():
    """Clean up bot state file when bot stops"""
    try:
        if STATE_FILE.exists():
            # Update state to not running instead of deleting
            save_bot_state(False)
            logger.info("🧹 Bot state cleaned up")
    except Exception as e:
        logger.error(f"❌ Error cleaning up bot state: {e}")
