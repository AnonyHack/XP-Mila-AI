from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import REQUIRED_CHANNELS, SUPPORT_GROUP, SOURCE_CODE_LINK

def build_main_menu():
    """Create inline keyboard for main menu."""
    keyboard = [
        [InlineKeyboardButton("💬 Chat with Your Sweetheart", callback_data="chat_worm")],
        [InlineKeyboardButton("❓ Get to Know Me", callback_data="help_page_1")],
        [InlineKeyboardButton("🗑️ Clear Our Chat", callback_data="clear")],
        [InlineKeyboardButton("ℹ️ About Your Girl", callback_data="about_page_1")],
    ]
    return InlineKeyboardMarkup(keyboard)

def build_join_channels_keyboard():
    """Create inline keyboard for channel joining."""
    keyboard = []
    for channel in REQUIRED_CHANNELS:
        keyboard.append([InlineKeyboardButton(f"📢 Join {channel['name']}", url=channel["url"])])
    keyboard.append([InlineKeyboardButton("✅ Verify Membership", callback_data="verify_membership")])
    return InlineKeyboardMarkup(keyboard)

def build_about_keyboard(page: int, total_pages: int):
    """Create inline keyboard for about menu."""
    keyboard = [
        [InlineKeyboardButton("📢 Our Love Nest (Support Group)", url=SUPPORT_GROUP)],
        [InlineKeyboardButton("📝 My Code (Source)", url=SOURCE_CODE_LINK)],
        [InlineKeyboardButton("🏠 Back to Main Page", callback_data="about_home")],
        [InlineKeyboardButton("❌ Close", callback_data="about_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_help_keyboard(page: int, total_pages: int):
    """Create inline keyboard for help menu."""
    keyboard = [
        [InlineKeyboardButton("ℹ️ About Your Girl", callback_data="about_page_1")],
        [InlineKeyboardButton("📢 Our Love Nest (Support Group)", url=SUPPORT_GROUP)],
        [InlineKeyboardButton("🏠 Back to Main Page", callback_data="about_home")],
    ]
    return InlineKeyboardMarkup(keyboard)