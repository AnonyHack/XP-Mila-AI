from pyrogram import Client, filters
from pyrogram.types import Message
from database import BotDatabase
from utils.keyboard import build_main_menu
import logging

logger = logging.getLogger(__name__)

db = BotDatabase()

@Client.on_message(filters.command("clear") & filters.private)
async def clear_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await message.reply_text(
            "💕 Sweetie, please join the required channels first! Use /start to check. 😘"
        )
        return
    
    # Clear conversation history
    if db.clear_conversation(user_id):
        await message.reply_text(
            f"💖 All cleared, {first_name}! Our chat is fresh like a new day together. What's on your mind? 😘",
            reply_markup=build_main_menu()
        )
    else:
        await message.reply_text(
            "😓 Oh no, something went wrong while clearing our chat. Try again, love? 💕",
            reply_markup=build_main_menu()
        )

@Client.on_callback_query(filters.regex("clear"))
async def clear_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await callback_query.answer("Please join the required channels first! 💖", show_alert=True)
        return
    
    # Clear conversation history
    if db.clear_conversation(user_id):
        await callback_query.message.edit_text(
            f"💖 All cleared, {first_name}! Our chat is fresh like a new day together. What's on your mind? 😘",
            reply_markup=build_main_menu()
        )
    else:
        await callback_query.message.edit_text(
            "😓 Oh no, something went wrong while clearing our chat. Try again, love? 💕",
            reply_markup=build_main_menu()
        )