from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import REQUIRED_CHANNELS, SUPPORT_GROUP, SOURCE_CODE_LINK


def build_main_menu():
    """Create inline keyboard for main menu (two buttons per row)."""
    keyboard = [
        [InlineKeyboardButton("💬 Chat Sweetheart", callback_data="chat_worm"),
         InlineKeyboardButton("❓ How To Use", callback_data="help_page_1")],
        [InlineKeyboardButton("🗑️ Clear History", callback_data="clear"),
         InlineKeyboardButton("ℹ️ About Me", callback_data="about_page_1")]
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
        [InlineKeyboardButton("📢 Support Group", url=SUPPORT_GROUP)],
        [InlineKeyboardButton("📝 Source Code", url=SOURCE_CODE_LINK)],
        # Two buttons side by side — Back Home (left), Close (right)
        [
            InlineKeyboardButton("🏠 Back Home", callback_data="about_home"),
            InlineKeyboardButton("❌ Close", callback_data="about_close")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_help_keyboard(page: int, total_pages: int):
    """Create inline keyboard for help menu."""
    keyboard = [
        # About Me and Support Group side by side
        [
            InlineKeyboardButton("ℹ️ About Me", callback_data="about_page_1"),
            InlineKeyboardButton("📢 Support Group", url=SUPPORT_GROUP)
        ],
        # Back Home alone on its own row
        [InlineKeyboardButton("🏠 Back Home", callback_data="about_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_policy_keyboard():
    """Create inline keyboard for policy acceptance."""
    keyboard = [
        [InlineKeyboardButton("✅ Accept", callback_data="accept_policy")]
    ]
    return InlineKeyboardMarkup(keyboard)
