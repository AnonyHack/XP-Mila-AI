from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import UserIsBlocked, PeerIdInvalid
from database import BotDatabase
from config import ADMIN_IDS
from loguru import logger
import asyncio
import datetime

db = BotDatabase()

async def broadcast_messages(client: Client, user_id: int, message: Message) -> tuple[bool, str]:
    """Send a broadcast message to a user and return status."""
    try:
        if message.media:
            await message.copy(
                chat_id=user_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await client.send_message(
                chat_id=user_id,
                text=message.text,
                entities=message.entities,
                parse_mode=enums.ParseMode.MARKDOWN
            )
        logger.debug(f"Successfully broadcasted to user {user_id}")
        return True, "Success"
    except UserIsBlocked:
        logger.info(f"User {user_id} has blocked the bot")
        return False, "Blocked"
    except PeerIdInvalid:
        logger.info(f"User {user_id} has deleted their account or is invalid")
        return False, "Deleted"
    except Exception as e:
        logger.error(f"Failed to broadcast to user {user_id}: {e}")
        return False, "Error"

@Client.on_message(filters.command("broadcast") & filters.private & filters.user(ADMIN_IDS))
async def broadcast_command(client: Client, message: Message):
    """Handle the /broadcast command with message content."""
    user_id = message.from_user.id
    logger.debug(f"Processing /broadcast for user {user_id}")

    # Extract message content (text or caption), removing /broadcast
    msg_text = None
    msg_entities = None
    if message.text:
        msg_text = message.text.replace("/broadcast", "", 1).strip()
        msg_entities = message.entities
    elif message.caption:
        msg_text = message.caption.replace("/broadcast", "", 1).strip()
        msg_entities = message.caption_entities

    # Check if message is valid
    if not msg_text and not message.media:
        logger.warning(f"Invalid broadcast message from user {user_id}")
        await message.reply_text(
            "⚠️ Please include a valid message with /broadcast (e.g., /broadcast *hello* or attach media with a caption).",
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return

    # Get all user IDs from database
    try:
        logger.info(f"Fetching user IDs for broadcast by user {user_id}")
        user_ids = db.get_all_users()
        total_users = len(user_ids)
        logger.info(f"Found {total_users} users for broadcast")
    except Exception as e:
        logger.error(f"Error fetching users for broadcast by user {user_id}: {e}", exc_info=True)
        await message.reply_text("⚠️ Error fetching users from database. Please try again later.")
        return

    if not user_ids:
        logger.info(f"No users found for broadcast by user {user_id}")
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
        pti, sh = await broadcast_messages(client, user_id, message)
        if pti:
            success += 1
        elif sh == "Blocked":
            blocked += 1
        elif sh == "Deleted":
            deleted += 1
        elif sh == "Error":
            failed += 1
        done += 1
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
            logger.debug(f"Broadcast progress: {done}/{total_users} by user {user_id}")
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
    logger.info(f"Broadcast completed for admin {user_id}: Success={success}, Blocked={blocked}, Deleted={deleted}, Failed={failed}")
