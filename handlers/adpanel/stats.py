from pyrogram import Client, filters, enums
from pyrogram.types import Message
from database import BotDatabase
from config import ADMIN_IDS, BOT_USERNAME, BOT_NAME
import logging

logger = logging.getLogger(__name__)

db = BotDatabase()

@Client.on_message(filters.command("stats") & filters.private, group=0)
async def stats_command(client: Client, message: Message):
    logger.debug(f"Processing /stats for user {message.from_user.id}")
    user_id = message.from_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_IDS:
        await message.reply_text("🚫 Sorry, only admins can use this command!")
        return
    
    try:
        # Get user stats
        total_users = len(db.get_all_users())
        active_users_7d = db.get_active_users_7d()
        new_users_24h = db.get_new_users_24h()
        
        # Get persistent conversation stats
        conv_counts = db.get_persistent_conversation_counts()
        
        # Format stats message in quoted style
        stats_message = (
            "<blockquote>\n"
            "⍟───[ ʙᴏᴛ sᴛᴀᴛɪꜱᴛɪᴄꜱ ]───⍟\n\n"
            f"‣ ʙᴏᴛ ɴᴀᴍᴇ: <a href=\"https://t.me/{BOT_USERNAME}\">{BOT_NAME}</a> 📊\n"
            f"‣ ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ: {total_users} 👤\n"
            f"‣ ᴀᴄᴛɪᴠᴇ ᴜꜱᴇʀꜱ (7ᴅ): {active_users_7d} 🔥\n"
            f"‣ ɴᴇᴡ ᴜꜱᴇʀꜱ (24ʜ): {new_users_24h} 🆕\n"
            f"‣ ᴄᴏɴᴠᴇʀꜱᴀᴛɪᴏɴꜱ (ᴛᴏᴛᴀʟ): {conv_counts['total']} 💬\n"
            f"‣ ᴄᴏɴᴠᴇʀꜱᴀᴛɪᴏɴꜱ (24ʜ): {conv_counts['24h']} 📍\n"
            f"‣ ᴄᴏɴᴠᴇʀꜱᴀᴛɪᴏɴꜱ (7ᴅ): {conv_counts['7d']} 📅\n"
            f"‣ ᴄᴏɴᴠᴇʀꜱᴀᴛɪᴏɴꜱ (30ᴅ): {conv_counts['30d']} 🗓️\n"
            "⍟────────────────────⍟\n"
            "</blockquote>"
        )
        
        await message.reply_text(stats_message, parse_mode=enums.ParseMode.HTML)
        logger.info(f"Stats displayed for user {user_id}")
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        await message.reply_text("⚠️ Error fetching statistics. Please try again later.")
