from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import UserIsBlocked, PeerIdInvalid
from database import BotDatabase
from config import ADMIN_IDS
import logging
import asyncio
import datetime

logger = logging.getLogger(__name__)

db = BotDatabase()

@Client.on_message(filters.command("broadcast") & filters.private, group=0)
async def broadcast_command(client: Client, message: Message):
    logger.debug(f"Processing /broadcast for user {message.from_user.id}")
    user_id = message.from_user.id
    
    # Check if user is an admin
    if user_id not in ADMIN_IDS:
        await message.reply_text("🚫 Sorry, only admins can use this command!")
        logger.info(f"Unauthorized /broadcast attempt by user {user_id}")
        return
    
    # Prompt for broadcast message
    b_msg = await client.ask(
        chat_id=message.from_user.id,
        text="📢 Now send me your broadcast message (supports formatting like *bold*, _italic_, etc.)."
    )
    
    # Check if message is valid
    if not b_msg.text and not b_msg.caption:
        await message.reply_text("⚠️ Please send a valid message with text or media!")
        return
    
    # Get message content and entities
    msg_text = b_msg.text or b_msg.caption
    msg_entities = b_msg.entities or b_msg.caption_entities
    
    # Get all user IDs from database
    try:
        user_ids = db.get_all_users()
        total_users = len(user_ids)
    except Exception as e:
        logger.error(f"Error fetching users for broadcast: {e}")
        await message.reply_text("⚠️ Error fetching users from database. Please try again later.")
        return
    
    if not user_ids:
        await message.reply_text("📭 No users found to broadcast to.")
        return
    
    # Initialize counters
    sts = await message.reply_text("📢 Broadcasting your message...")
    start_time = datetime.datetime.now()
    done = 0
    success = 0
    blocked = 0
    deleted = 0
    failed = 0
    
    # Send broadcast to each user
    for user_id in user_ids:
        try:
            if b_msg.media:
                # Handle media messages (photo, video, etc.) with caption
                await b_msg.copy(
                    chat_id=user_id,
                    caption=msg_text,
                    caption_entities=msg_entities,
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            else:
                # Handle text messages
                await client.send_message(
                    chat_id=user_id,
                    text=msg_text,
                    entities=msg_entities,
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            success += 1
        except UserIsBlocked:
            logger.debug(f"User {user_id} blocked the bot")
            blocked += 1
        except PeerIdInvalid:
            logger.debug(f"User {user_id} has deleted their account or is invalid")
            deleted += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user_id}: {e}")
            failed += 1
        done += 1
        
        # Update progress every 20 users
        if done % 20 == 0:
            await sts.edit_text(
                f"📢 Broadcast in progress:\n\n"
                f"Total Users: {total_users}\n"
                f"Completed: {done} / {total_users}\n"
                f"Success: {success}\n"
                f"Blocked: {blocked}\n"
                f"Deleted: {deleted}\n"
                f"Failed: {failed}"
            )
        await asyncio.sleep(0.1)  # Avoid rate limits
    
    # Final report
    time_taken = datetime.datetime.now() - start_time
    await sts.edit_text(
        f"📢 Broadcast Completed:\n"
        f"Completed in {time_taken.total_seconds():.2f} seconds.\n\n"
        f"Total Users: {total_users}\n"
        f"Completed: {done} / {total_users}\n"
        f"Success: {success}\n"
        f"Blocked: {blocked}\n"
        f"Deleted: {deleted}\n"
        f"Failed: {failed}"
    )
    logger.info(f"Broadcast completed for admin {user_id}: {success} succeeded, {blocked} blocked, {deleted} deleted, {failed} failed")
