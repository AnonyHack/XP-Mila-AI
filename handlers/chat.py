from pyrogram import Client, filters
from pyrogram.types import Message
from database import BotDatabase
from core.ai_client import VeniceAI
from utils.keyboard import build_main_menu
from config import BOT_USERNAME
import logging

logger = logging.getLogger(__name__)

db = BotDatabase()
ai_client = VeniceAI()

@Client.on_callback_query(filters.regex("chat_worm"))
async def chat_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await callback_query.answer("Please join the required channels first! 💖", show_alert=True)
        return
    
    # Keep the main menu buttons for the initial chat prompt
    await callback_query.message.edit_text(
        f"💬 Alright, {first_name}, let’s have a little heart-to-heart! 😘 What’s on your mind?",
        reply_markup=build_main_menu()
    )

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "clear", "profile", "menu"]))
async def chat_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await message.reply_text(
            "💕 Sweetie, please join the required channels first! Use /start to check. 😘",
            reply_markup=build_main_menu()
        )
        return
    
    # Get user input and conversation history
    user_input = message.text.replace(f"@{BOT_USERNAME}", "").strip()
    history = db.get_conversation_history(user_id)
    
    # Generate AI response
    response = ai_client.get_ai_response(history, user_input, first_name)
    
    # Save conversation
    db.add_conversation(user_id, "user", user_input)
    db.add_conversation(user_id, "assistant", response)
    
    # Send response without buttons
    await message.reply_text(response)

@Client.on_message(filters.command("menu") & filters.private)
async def menu_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await message.reply_text(
            "💕 Sweetie, please join the required channels first! Use /start to check. 😘",
            reply_markup=build_main_menu()
        )
        return
    
    # Send main menu with buttons
    await message.reply_text(
        f"💕 Hey {first_name}, here's our little love hub! 😘 Pick an option to continue our journey!",
        reply_markup=build_main_menu()
    )