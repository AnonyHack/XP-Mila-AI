from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from database import BotDatabase
from core.ai_client import VeniceAI
from utils.keyboard import build_main_menu
from utils.image_gallery import image_gallery
from config import BOT_USERNAME, WELCOME_IMAGE
import logging
import asyncio
import re

logger = logging.getLogger(__name__)

db = BotDatabase()
ai_client = VeniceAI()

# Patterns to detect image requests
IMAGE_PATTERNS = [
    r'send.*pic(ture)?', r'show.*pic(ture)?', r'can.*see.*pic(ture)?',
    r'want.*pic(ture)?', r'have.*pic(ture)?', r'share.*pic(ture)?',
    r'send.*image', r'show.*image', r'want.*image',
    r'send.*photo', r'show.*photo', r'want.*photo',
    r'send.*selfie', r'show.*selfie', r'want.*selfie',
    r'what.*look like', r'how.*look', r'see.*face',
    r'pic(ture)?.*please', r'image.*please', r'photo.*please',
    r'picture\?', r'photo\?', r'selfie\?',
    r'give.*pic', r'give.*photo', r'give.*image',
    r'let.*see.*pic', r'let.*see.*photo',
    r'can.*have.*pic', r'can.*have.*photo',
    r'may.*see.*pic', r'may.*see.*photo',
    r'would.*love.*pic', r'would.*love.*photo',
    r'love.*see.*pic', r'love.*see.*photo',
    r'pic$', r'photo$', r'selfie$', r'image$',
    r'generate.*pic', r'create.*pic', r'make.*pic',
    r'draw.*pic', r'draw.*me'
]

# Category detection patterns
CATEGORY_PATTERNS = {
    'cute': [r'cute', r'adorable', r'sweet', r'kawaii', r'pretty', r'lovely'],
    'romantic': [r'romantic', r'love', r'couple', r'date', r'heart', r'relationship'],
    'anime': [r'anime', r'cartoon', r'drawing', r'art', r'manga', r'character'],
    'selfie': [r'selfie', r'yourself', r'you', r'face', r'real', r'actual']
}

def detect_image_request(text: str) -> bool:
    """Check if user is asking for an image"""
    text_lower = text.lower().strip()
    
    # Check single word requests first
    if text_lower in ['pic', 'photo', 'selfie', 'picture', 'image']:
        return True
        
    for pattern in IMAGE_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

def detect_category(text: str) -> str:
    """Detect what type of image user wants"""
    text_lower = text.lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return category
    return None

async def send_image_with_fallback(client: Message, image_url: str, caption: str):
    """Try to send image with multiple fallback strategies"""
    try:
        # First try: Send the image URL
        await client.reply_photo(
            photo=image_url,
            caption=caption
        )
        return True
        
    except Exception as e:
        logger.warning(f"First image send failed: {e}, trying fallback...")
        
        try:
            # Second try: Use the bot's welcome image as fallback
            await client.reply_photo(
                photo=WELCOME_IMAGE,
                caption=f"{caption} (Here's a special picture for you! 💕)"
            )
            return True
            
        except Exception as e2:
            logger.error(f"All image sending failed: {e2}")
            return False

@Client.on_callback_query(filters.regex("chat_mila"))
async def chat_callback(client: Client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name or "darling"
    
    # Check if user is verified
    if not db.is_user_verified(user_id):
        await callback_query.answer("Please join the required channels first! 💖", show_alert=True)
        return
    
    # Keep the main menu buttons for the initial chat prompt
    await callback_query.message.edit_text(
        f"💬 Alright, {first_name}, let's have a little heart-to-heart! 😘 What's on your mind?",
        reply_markup=build_main_menu()
    )

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "clear", "profile", "menu", "broadcast", "stats", "policy"]))
async def chat_command(client: Client, message: Message):
    logger.debug(f"Processing chat message from user {message.from_user.id}: {message.text}")
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
    
    # Check if user is asking for an image
    if detect_image_request(user_input):
        category = detect_category(user_input)
        
        # Send initial response
        thinking_msg = await message.reply_text("💖 Let me create a special picture just for you, darling! 🎨✨")
        
        try:
            # Send typing action
            await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)
            
            # Generate AI image (this might take a few seconds)
            image_url = await image_gallery.get_image(
                category=category, 
                user_input=user_input,
                use_ai=True  # Enable AI generation
            )
            
            # Delete the thinking message
            await thinking_msg.delete()
            
            # Cute responses based on category
            responses = {
                'cute': "I made this cute picture especially for you, sweetie! Hope it makes you smile! 😊💕",
                'romantic': "I created this romantic image thinking of us! You're always in my heart! 💖🌹",
                'anime': "I drew this anime-style picture just for you! Hope you love it as much as I loved making it! 🎨✨",
                'selfie': "This is how I imagine myself when I think of you! Created this selfie specially for my favorite person! 💁‍♀️💗",
                None: "I made this special picture just for you, darling! Put all my love into creating it! 📸💝"
            }
            
            caption = responses.get(category, responses[None])
            
            # Try to send the generated image
            success = await send_image_with_fallback(message, image_url, caption)
            
            if success:
                logger.info(f"✅ Sent AI-generated image to user {user_id} (category: {category})")
                
                # TRACK THE IMAGE GENERATION - ADD THIS LINE
                image_type = "ai_generated" if "pollinations.ai" in image_url else "static"
                db.add_image_generation(user_id, category or "general", image_type, success=True)
                
                # Save to conversation history
                db.add_conversation(user_id, "user", user_input)
                db.add_conversation(user_id, "assistant", f"[Created and sent a picture] {caption}")
                return
            else:
                # Track failed attempt
                db.add_image_generation(user_id, category or "general", "failed", success=False)
                raise Exception("All image sending methods failed")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate/send image: {e}")
            # Delete thinking message if it still exists
            try:
                await thinking_msg.delete()
            except:
                pass
            
            # Track failed attempt
            db.add_image_generation(user_id, category or "general", "failed", success=False)
            
            # Fall back to cute text response
            fallback_response = "I tried to create a beautiful picture for you, sweetie, but my artistic skills are taking a break right now! 😔 How about I tell you how incredibly special you are instead? You mean the world to me! 💕✨"
            await message.reply_text(fallback_response)
            
            # Save to conversation history
            db.add_conversation(user_id, "user", user_input)
            db.add_conversation(user_id, "assistant", fallback_response)
            return
    
    # Normal AI chat response
    try:
        # Send typing action
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        # Generate AI response
        response = ai_client.get_ai_response(history, user_input, first_name)
        
        # Save conversation
        db.add_conversation(user_id, "user", user_input)
        db.add_conversation(user_id, "assistant", response)
        
        # Send response without buttons
        await message.reply_text(response)
        logger.info(f"AI responded to user {user_id}: {response[:50]}...")
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        error_response = "I'm feeling a bit shy right now, sweetie. Can we try again in a moment? 😔💕"
        await message.reply_text(error_response)

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
    logger.info(f"Displayed menu for user {user_id}")
