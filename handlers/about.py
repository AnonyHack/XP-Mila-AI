from pyrogram import Client, filters, enums
from pyrogram.types import InputMediaPhoto
from database import BotDatabase
from utils.keyboard import build_about_keyboard, build_main_menu
from config import BOT_NAME, BOT_USERNAME, OWNER_USERNAME, WELCOME_IMAGE, WELCOME_MESSAGE
import logging

logger = logging.getLogger(__name__)

db = BotDatabase()

# Single about page
ABOUT_PAGE = """
<blockquote>
⍟───[ ᴍʏ ᴅᴇᴛᴀɪʟꜱ ]───⍟

‣ ᴍʏ ɴᴀᴍᴇ : <a href="https://t.me/{bot_username}">{BOT_NAME}</a> 🔍
‣ ᴍʏ ʙᴇsᴛ ғʀɪᴇɴᴅ : <a href="tg://settings">ᴛʜɪs ᴘᴇʀsᴏɴ</a>
‣ ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href="https://t.me/{owner_username}">ᴅᴇᴠ</a>
‣ ʟɪʙʀᴀʀʏ : <a href="https://docs.pyrogram.org/">ᴘʏʀᴏɢʀᴀᴍ</a>
‣ ʟᴀɴɢᴜᴀɢᴇ : <a href="https://www.python.org/download/releases/3.0/">ᴘʏᴛʜᴏɴ 3</a>
‣ ᴅᴀᴛᴀ ʙᴀsᴇ : <a href="https://www.mongodb.com/">ᴍᴏɴɢᴏ ᴅʙ</a>
‣ ʙᴏᴛ sᴇʀᴠᴇʀ : <a href="https://render.com/">ʀᴇɴᴅᴇʀ</a>
‣ ʙᴜɪʟᴅ sᴛᴀᴛᴜs : <a href="#">ᴠ1.0 [sᴛᴀʙʟᴇ]</a>
⍟────────────────────⍟
</blockquote>
"""

@Client.on_callback_query(filters.regex(r"about_page_1"))
async def about_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await callback_query.answer("Please join the required channels first! 💖", show_alert=True)
        return
    
    # Format about text
    try:
        bot_username = BOT_USERNAME.lstrip('@') if BOT_USERNAME else "unknown"
        owner_username = OWNER_USERNAME.lstrip('@') if OWNER_USERNAME else "unknown"
        about_text = ABOUT_PAGE.format(
            BOT_NAME=BOT_NAME,
            bot_username=bot_username,
            owner_username=owner_username
        )
        
        # Update media and caption in one call
        await callback_query.message.edit_media(
            media=InputMediaPhoto(WELCOME_IMAGE, caption=about_text, parse_mode=enums.ParseMode.HTML),
            reply_markup=build_about_keyboard(1, 1)  # Single page
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error updating about message: {e}")
        await callback_query.message.edit_text(
            text=about_text,
            reply_markup=build_about_keyboard(1, 1),
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()

@Client.on_callback_query(filters.regex("about_home"))
async def about_home_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await callback_query.answer("Please join the required channels first! 💖", show_alert=True)
        return
    
    # Return to main menu
    try:
        await callback_query.message.edit_media(
            media=InputMediaPhoto(WELCOME_IMAGE, caption=WELCOME_MESSAGE.format(user_name=first_name), parse_mode=enums.ParseMode.HTML),
            reply_markup=build_main_menu()
        )
        await callback_query.answer("✅ Returned to main menu!")
    except Exception as e:
        logger.error(f"Error editing welcome message: {e}")
        await callback_query.message.edit_text(
            text=WELCOME_MESSAGE.format(user_name=first_name),
            reply_markup=build_main_menu(),
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer("✅ Returned to main menu!")

@Client.on_callback_query(filters.regex("about_close"))
async def about_close_callback(client: Client, callback_query):
    try:
        await callback_query.message.delete()
        await callback_query.answer("💕 Chat closed, but I’m always here for you, love! 😘")
    except Exception as e:
        logger.error(f"Error closing about: {e}")

        await callback_query.answer("Something went wrong, sweetie. Try again? 💖", show_alert=True)
