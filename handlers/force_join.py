from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant
from database import BotDatabase
from utils.keyboard import build_main_menu
from config import WELCOME_IMAGE, WELCOME_MESSAGE, REQUIRED_CHANNELS
import logging

logger = logging.getLogger(__name__)

db = BotDatabase()

async def is_user_member(client: Client, user_id: int) -> bool:
    """Check if user is member of all required channels."""
    for ch in REQUIRED_CHANNELS:
        chat = ch.get("chat_id")  # Use chat_id (username or ID)
        try:
            # Handle both channel IDs and usernames
            if str(chat).startswith('-100'):
                chat_id = int(chat)
            else:
                chat_id = chat.lstrip('@')  # Remove @ if present
                
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [enums.ChatMemberStatus.MEMBER, 
                                   enums.ChatMemberStatus.ADMINISTRATOR, 
                                   enums.ChatMemberStatus.OWNER]:
                logger.info(f"User {user_id} not a member of {ch['name']}")
                return False
        except UserNotParticipant:
            logger.info(f"User {user_id} not participant in {ch['name']}")
            return False
        except Exception as e:
            logger.error(f"Error checking membership for {ch['name']}: {e}")
            return False
    logger.info(f"User {user_id} verified for all required channels")
    return True

async def ask_user_to_join(client: Client, message):
    """Ask user to join required channels."""
    buttons = [[InlineKeyboardButton(ch["name"], url=ch["url"])] for ch in REQUIRED_CHANNELS]
    buttons.append([InlineKeyboardButton("✅ Verify Membership", callback_data="verify_membership")])
    
    await message.reply(
        "💕 Hey sweetie, to start chatting with me, please join these channels first! 😘\n"
        "Click the buttons below to join, then press '✅ Verify Membership' to continue.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("verify_membership"))
async def refresh_join_status(client: Client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name or "darling"
    
    if await is_user_member(client, user_id):
        db.verify_user(user_id)
        await callback_query.message.delete()
        try:
            await callback_query.message.reply_photo(
                photo=WELCOME_IMAGE,
                caption=WELCOME_MESSAGE.format(user_name=first_name),
                reply_markup=build_main_menu()
            )
        except Exception as e:
            logger.error(f"Error sending welcome photo: {e}")
            await callback_query.message.reply_text(
                WELCOME_MESSAGE.format(user_name=first_name),
                reply_markup=build_main_menu()
            )
    else:
        await callback_query.answer("❌ You haven't joined all channels yet! 💖", show_alert=True)