from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto
from database import BotDatabase
from utils.keyboard import build_main_menu
from config import WELCOME_MESSAGE, WELCOME_IMAGE
from handlers.force_join import ask_user_to_join, is_user_member
import logging

logger = logging.getLogger(__name__)

db = BotDatabase()

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Add user to database
    db.add_user(user_id, username, first_name, last_name)
    
    # Check channel membership
    is_member = await is_user_member(client, user_id)
    
    if not is_member:
        await ask_user_to_join(client, message)
        return
    
    # Mark user as verified
    db.verify_user(user_id)
    
    # Send welcome message with image
    try:
        await message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=WELCOME_MESSAGE.format(user_name=first_name or "darling"),
            reply_markup=build_main_menu()
        )
    except Exception as e:
        logger.error(f"Error sending welcome photo: {e}")
        await message.reply_text(
            WELCOME_MESSAGE.format(user_name=first_name or "darling"),
            reply_markup=build_main_menu()
        )

@Client.on_callback_query(filters.regex("start"))
async def start_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    
    # Check channel membership
    is_member = await is_user_member(client, user_id)
    
    if not is_member:
        await ask_user_to_join(client, callback_query.message)
        return
    
    # Update message with main menu
    try:
        await callback_query.message.edit_media(
            media=InputMediaPhoto(WELCOME_IMAGE),
            caption=WELCOME_MESSAGE.format(user_name=first_name or "darling"),
            reply_markup=build_main_menu()
        )
    except Exception as e:
        logger.error(f"Error editing welcome photo: {e}")
        await callback_query.message.edit_text(
            WELCOME_MESSAGE.format(user_name=first_name or "darling"),
            reply_markup=build_main_menu()
        )