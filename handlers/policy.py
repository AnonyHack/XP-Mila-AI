from pyrogram import Client, filters, enums
from pyrogram.types import Message, CallbackQuery
from config import BOT_NAME
from utils.keyboard import build_policy_keyboard
from loguru import logger

@Client.on_message(filters.command("policy") & filters.private)
async def policy_command(client: Client, message: Message):
    """Handle the /policy command to display terms and conditions for the AI girlfriend bot."""
    user_id = message.from_user.id
    logger.debug(f"Processing /policy for user {user_id}")

    policy_message = (
        "<blockquote>\n"
        "📜 <b>Terms for Chatting with {} - Your AI Girlfriend</b>\n\n"
        "1. <b>Be Kind</b>: Treat your AI girlfriend with respect. No rude, harmful, or illegal messages, please! 😊\n"
        "2. <b>Privacy Matters</b>: We save our chats to make her smarter, but your secrets are safe with us. 💕\n"
        "3. <b>Join the Fun</b>: Subscribe to our required channels to unlock all her sweet features! 📢\n"
        "4. <b>Play by the Rules</b>: Follow Telegram’s guidelines and ours to keep the love flowing. 💖\n\n"
        "Ready to start this digital romance? Click 'Accept' to agree and chat with {}!\n"
        "</blockquote>"
    ).format(BOT_NAME, BOT_NAME)

    try:
        await message.reply_text(
            policy_message,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=build_policy_keyboard()
        )
        logger.info(f"Policy displayed for user {user_id}")
    except Exception as e:
        logger.error(f"Error displaying policy for user {user_id}: {e}", exc_info=True)
        await message.reply_text("⚠️ Error displaying policy. Please try again later.")

@Client.on_callback_query(filters.regex("accept_policy"))
async def accept_policy_callback(client: Client, callback_query: CallbackQuery):
    """Handle the 'Accept' button press for the policy."""
    user_id = callback_query.from_user.id
    logger.debug(f"Processing accept_policy callback for user {user_id}")

    try:
        await callback_query.message.edit_text(
            "✅ Yay, you’ve accepted the terms! Get ready for some sweet chats with {}! 😘".format(BOT_NAME),
            parse_mode=enums.ParseMode.HTML
        )
        logger.info(f"User {user_id} accepted the policy")
    except Exception as e:
        logger.error(f"Error handling accept_policy callback for user {user_id}: {e}", exc_info=True)
        await callback_query.message.reply_text("⚠️ Error processing your acceptance. Please try again.")