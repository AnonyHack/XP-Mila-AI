from pyrogram import Client, filters
from pyrogram.types import Message
from database import BotDatabase
from utils.keyboard import build_main_menu
import logging

logger = logging.getLogger(__name__)

db = BotDatabase()

@Client.on_message(filters.command("profile") & filters.private)
async def profile_command(client: Client, message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await message.reply_text(
            "💕 Sweetie, please join the required channels first! Use /start to check. 😘",
            reply_markup=build_main_menu()
        )
        return
    
    # Get current preferences
    preferences = db.get_preferences(user_id)
    current_nickname = preferences.get("nickname", first_name)
    current_traits = preferences.get("traits", "flirty and caring")
    
    # Parse new preferences from command (e.g., /profile nickname=Love traits=playful,romantic)
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    new_prefs = {}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            new_prefs[key.lower()] = value
    
    # Update preferences if provided
    if new_prefs:
        if db.update_preferences(user_id, new_prefs):
            await message.reply_text(
                f"💖 Oh, {first_name}, you’ve updated our vibe! I’ll call you {new_prefs.get('nickname', current_nickname)} and be {new_prefs.get('traits', current_traits)}. Ready to chat, my love? 😘",
                reply_markup=build_main_menu()
            )
        else:
            await message.reply_text(
                "😓 Something went wrong updating your profile, sweetie. Try again? 💕",
                reply_markup=build_main_menu()
            )
    else:
        # Show current preferences
        await message.reply_text(
            f"💕 Here’s how I see you, {current_nickname}:\n"
            f"✨ Nickname: {current_nickname}\n"
            f"🌹 Personality: {current_traits}\n"
            f"Change it with /profile nickname=Love traits=playful,romantic",
            reply_markup=build_main_menu()
        )