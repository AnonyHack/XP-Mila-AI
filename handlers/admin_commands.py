from pyrogram import Client, filters, enums
from pyrogram.types import Message
from database import BotDatabase
from config import ADMIN_IDS
import logging
import asyncio

logger = logging.getLogger(__name__)

db = BotDatabase()

@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_IDS:
        await message.reply_text("🚫 Sorry, only admins can use this command!")
        return
    
    # Check if broadcast message is provided
    if len(message.text.split()) < 2:
        await message.reply_text("📢 Please provide a message to broadcast! Usage: /broadcast <message>")
        return
    
    # Get broadcast message (remove command part)
    broadcast_message = " ".join(message.text.split()[1:])
    
    # Get all user IDs from database
    try:
        user_ids = db.get_all_users()
    except Exception as e:
        logger.error(f"Error fetching users for broadcast: {e}")
        await message.reply_text("⚠️ Error fetching users from database. Please try again later.")
        return
    
    if not user_ids:
        await message.reply_text("📭 No users found to broadcast to.")
        return
    
    success_count = 0
    failure_count = 0
    
    # Send broadcast to each user
    for user_id in user_ids:
        try:
            await client.send_message(
                chat_id=user_id,
                text=broadcast_message,
                parse_mode=enums.ParseMode.HTML
            )
            success_count += 1
            await asyncio.sleep(0.1)  # Small delay to avoid rate limits
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user_id}: {e}")
            failure_count += 1
            continue
    
    # Report results to admin
    await message.reply_text(
        f"📢 Broadcast completed!\n"
        f"✅ Sent to {success_count} users\n"
        f"❌ Failed for {failure_count} users"
    )

@Client.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
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
        
        # Get conversation stats
        conv_counts = db.get_conversation_counts()
        
        # Format stats message
        stats_message = (
            "👥 Uꜱᴇʀ Sᴛᴀᴛɪꜱᴛɪᴄꜱ\n"
            f"├ 👤 Tᴏᴛᴀʟ Uꜱᴇʀꜱ: {total_users}\n"
            f"├ 🔥 Aᴄᴛɪᴠᴇ (7ᴅ): {active_users_7d}\n"
            f"├ 🆕 Nᴇᴡ (24ʜ): {new_users_24h}\n"
            "└ 💬 Cᴏɴᴠᴇʀꜱᴀᴛɪᴏɴꜱ\n"
            f"    ├ 📍 24ʜ: {conv_counts['24h']}\n"
            f"    ├ 📅 7ᴅ: {conv_counts['7d']}\n"
            f"    └ 🗓️ 30ᴅ: {conv_counts['30d']}"
        )
        
        await message.reply_text(stats_message, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        await message.reply_text("⚠️ Error fetching statistics. Please try again later.")