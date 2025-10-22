from pyrogram import Client, filters, enums
from pyrogram.types import InputMediaPhoto
from database import BotDatabase
from utils.keyboard import build_help_keyboard
from config import BOT_NAME, OWNER_USERNAME, WELCOME_IMAGE
import logging

logger = logging.getLogger(__name__)

db = BotDatabase()

# Single help page
HELP_PAGE = """
💕 Hey {first_name}, here's how to make our time together even sweeter! 😘<br><br>
🤖 <b>{BOT_NAME} - Help</b><br><br>
✨ <b>Commands:</b><br>
  /start - Kick off our romantic journey<br>
  /clear - Clear our chat history for a fresh start<br>
  /profile - Set your nickname or tweak my vibe (e.g., /profile nickname=Love traits=playful)<br><br>
✨ <b>How to use:</b><br>
  1. Use /start to join my world<br>
  2. Join the required channel to unlock our chats<br>
  3. Click "Chat with Your Sweetheart" to flirt with me<br>
  4. Use /clear or the "Clear Our Chat" button to reset<br>
  5. Click "About Your Girl" for my secrets<br><br>
💖 <b>Developer:</b> <a href="https://t.me/{owner_username}">{BOT_NAME}</a>
"""

@Client.on_callback_query(filters.regex(r"help_page_1"))
async def help_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await callback_query.answer("Please join the required channels first! 💖", show_alert=True)
        return
    
    # Format help text
    try:
        owner_username = OWNER_USERNAME.lstrip('@') if OWNER_USERNAME else "unknown"
        help_text = HELP_PAGE.format(
            first_name=first_name,
            BOT_NAME=BOT_NAME,
            owner_username=owner_username
        )
        
        # Update media and caption in one call
        await callback_query.message.edit_media(
            media=InputMediaPhoto(WELCOME_IMAGE, caption=help_text, parse_mode=enums.ParseMode.HTML),
            reply_markup=build_help_keyboard(1, 1)  # Single page, so page=1, total_pages=1
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error updating help message: {e}")
        await callback_query.message.edit_text(
            text=help_text,
            reply_markup=build_help_keyboard(1, 1),
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()