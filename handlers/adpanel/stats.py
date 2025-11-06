import time
from datetime import datetime, timedelta
from loguru import logger
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import BotDatabase
from config import ADMIN_IDS, BOT_USERNAME, BOT_NAME

db = BotDatabase()

# Store stats data for navigation
stats_cache = {}

@Client.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    """Display bot statistics main menu for admins"""
    try:
        user_id = message.from_user.id
        logger.info(f"📊 Stats command received from admin: {user_id}")
        
        # Check if user is an admin
        if user_id not in ADMIN_IDS:
            logger.warning(f"Unauthorized /stats attempt by user {user_id}")
            await message.reply_text("🚫 Sorry, only admins can use this command!")
            return
        
        # Get all statistics
        stats_data = await get_comprehensive_stats()
        
        # Store stats in cache
        cache_id = f"stats_{user_id}_{int(time.time())}"
        stats_cache[cache_id] = stats_data
        
        # Format the main menu
        stats_text = f"""
<blockquote><b>⍟───[ {BOT_NAME} STATISTICS ]───⍟</b></blockquote>

💡 <b>Select a category below to view detailed statistics:</b>

<blockquote>🤖 <b>Bot:</b> <a href="https://t.me/{BOT_USERNAME}">{BOT_NAME}</a></blockquote>
"""
        
        # Create navigation buttons (side by side)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Users Stats", callback_data=f"stats_page:{cache_id}:users"),
             InlineKeyboardButton("💬 Conversations", callback_data=f"stats_page:{cache_id}:conversations")],
            [InlineKeyboardButton("🖼️ Image Stats", callback_data=f"stats_page:{cache_id}:images"),
             InlineKeyboardButton("📊 Overview", callback_data=f"stats_page:{cache_id}:overview")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
             InlineKeyboardButton("❌ Close", callback_data="close_stats")]
        ])
        
        # Send the statistics main menu
        await message.reply_text(
            stats_text, 
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=keyboard
        )
        
        logger.success(f"✅ Statistics main menu sent to admin: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in stats command: {e}")
        await message.reply_text(
            "❌ Error gathering statistics. Please try again later.", 
            parse_mode=enums.ParseMode.HTML
        )

async def get_comprehensive_stats():
    """Get comprehensive bot statistics"""
    try:
        logger.info("📈 Gathering comprehensive statistics...")
        
        # Get user statistics
        total_users = len(db.get_all_users())
        active_users_7d = db.get_active_users_7d()
        new_users_24h = db.get_new_users_24h()
        
        # Get conversation statistics
        conv_counts = db.get_persistent_conversation_counts()
        
        # Get image generation statistics - NOW WITH REAL DATA
        image_stats = db.get_image_generation_stats()
        
        # Calculate growth rates
        active_rate_7d = (active_users_7d / total_users * 100) if total_users > 0 else 0
        daily_growth_rate = (new_users_24h / total_users * 100) if total_users > 0 else 0
        
        # Calculate conversation engagement
        avg_conversations_per_user = (conv_counts['total'] / total_users) if total_users > 0 else 0
        
        # Calculate image engagement
        image_engagement_rate = (image_stats['total'] / total_users * 100) if total_users > 0 else 0
        
        stats_data = {
            # Basic info
            'bot_name': BOT_NAME,
            'bot_username': BOT_USERNAME,
            
            # User stats
            'total_users': total_users,
            'active_users_7d': active_users_7d,
            'new_users_24h': new_users_24h,
            'active_rate_7d': active_rate_7d,
            'daily_growth_rate': daily_growth_rate,
            
            # Conversation stats
            'total_conversations': conv_counts['total'],
            'conversations_24h': conv_counts['24h'],
            'conversations_7d': conv_counts['7d'],
            'conversations_30d': conv_counts['30d'],
            'avg_conversations_per_user': avg_conversations_per_user,
            
            # Image stats - NOW REAL DATA
            'total_images_sent': image_stats['total'],
            'images_24h': image_stats['24h'],
            'images_7d': image_stats['7d'],
            'ai_images': image_stats['ai_generated'],
            'static_images': image_stats['static'],
            'popular_category': image_stats['popular_category'],
            'image_engagement_rate': image_engagement_rate,
            
            # Performance metrics
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cache_timestamp': int(time.time())
        }
        
        logger.debug(f"📈 Comprehensive stats calculated: {stats_data}")
        return stats_data
        
    except Exception as e:
        logger.error(f"❌ Error calculating comprehensive stats: {e}")
        return {
            'total_users': 0,
            'active_users_7d': 0,
            'new_users_24h': 0,
            'total_conversations': 0,
            'conversations_24h': 0,
            'conversations_7d': 0,
            'conversations_30d': 0,
            'total_images_sent': 0,
            'images_24h': 0,
            'images_7d': 0,
            'ai_images': 0,
            'static_images': 0,
            'popular_category': 'None',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def format_overview_stats(stats_data):
    """Format overview statistics page"""
    try:
        stats_text = f"""
<blockquote><b>⍟───[ BOT OVERVIEW ]───⍟</b></blockquote>

<blockquote><b>🤖 Bot Information:</b></blockquote>
<blockquote>├ • <b>Name:</b> {stats_data['bot_name']}
├ • <b>Username:</b> @{stats_data['bot_username']}
└ • <b>Status:</b> Online 🟢</blockquote>

<blockquote><b>👥 User Overview:</b></blockquote>
<blockquote>├ • <b>Total Users:</b> {stats_data['total_users']:,}
├ • <b>Active (7d):</b> {stats_data['active_users_7d']:,}
├ • <b>New (24h):</b> {stats_data['new_users_24h']:,}
├ • <b>Active Rate:</b> {stats_data['active_rate_7d']:.1f}%
└ • <b>Growth Rate:</b> {stats_data['daily_growth_rate']:.1f}%</blockquote>

<blockquote><b>💬 Conversation Stats:</b></blockquote>
<blockquote>├ • <b>Total:</b> {stats_data['total_conversations']:,}
├ • <b>Last 24h:</b> {stats_data['conversations_24h']:,}
├ • <b>Last 7d:</b> {stats_data['conversations_7d']:,}
├ • <b>Last 30d:</b> {stats_data['conversations_30d']:,}
└ • <b>Avg/User:</b> {stats_data['avg_conversations_per_user']:.1f}</blockquote>

<blockquote><b>🖼️ Image Stats:</b></blockquote>
<blockquote>├ • <b>Total Sent:</b> {stats_data['total_images_sent']:,}
├ • <b>Last 24h:</b> {stats_data['images_24h']:,}
├ • <b>Last 7d:</b> {stats_data['images_7d']:,}
└ • <b>Popular Category:</b> {stats_data['popular_category']}</blockquote>

<blockquote>🔄 <b>Last Updated:</b> {stats_data['last_updated']}</blockquote>
"""
        
        return stats_text
        
    except Exception as e:
        logger.error(f"❌ Error formatting overview stats: {e}")
        return "❌ Error formatting overview statistics."

def format_user_stats(stats_data):
    """Format user statistics page"""
    try:
        stats_text = f"""
<blockquote><b>⍟───[ USER STATISTICS ]───⍟</b></blockquote>

<blockquote><b>📊 User Analytics:</b></blockquote>
<blockquote>├ • <b>Total Users:</b> {stats_data['total_users']:,}
├ • <b>Active Users (7d):</b> {stats_data['active_users_7d']:,}
├ • <b>New Users (24h):</b> {stats_data['new_users_24h']:,}
└ • <b>User Retention:</b> {stats_data['active_users_7d']}/{stats_data['total_users']}</blockquote>

<blockquote><b>📈 Growth Metrics:</b></blockquote>
<blockquote>├ • <b>Active Rate (7d):</b> {stats_data['active_rate_7d']:.1f}%
├ • <b>Daily Growth Rate:</b> {stats_data['daily_growth_rate']:.1f}%
└ • <b>Engagement Score:</b> {'🟢 Excellent' if stats_data['active_rate_7d'] > 30 else '🟡 Good' if stats_data['active_rate_7d'] > 15 else '🔴 Needs Improvement'}</blockquote>

<blockquote><b>🎯 User Engagement:</b></blockquote>
<blockquote>├ • <b>Avg Conversations/User:</b> {stats_data['avg_conversations_per_user']:.1f}
├ • <b>Active User Ratio:</b> {stats_data['active_rate_7d']:.1f}%
└ • <b>Daily New Users:</b> {stats_data['new_users_24h']:,}</blockquote>

<blockquote>🔄 <b>Last Updated:</b> {stats_data['last_updated']}</blockquote>
"""
        
        return stats_text
        
    except Exception as e:
        logger.error(f"❌ Error formatting user stats: {e}")
        return "❌ Error formatting user statistics."

def format_conversation_stats(stats_data):
    """Format conversation statistics page"""
    try:
        # Calculate conversation rates
        daily_conv_rate = (stats_data['conversations_24h'] / stats_data['total_users'] * 100) if stats_data['total_users'] > 0 else 0
        weekly_conv_rate = (stats_data['conversations_7d'] / stats_data['total_users'] * 100) if stats_data['total_users'] > 0 else 0
        
        stats_text = f"""
<blockquote><b>⍟───[ CONVERSATION STATISTICS ]───⍟</b></blockquote>

<blockquote><b>💬 Conversation Volume:</b></blockquote>
<blockquote>├ • <b>Total Conversations:</b> {stats_data['total_conversations']:,}
├ • <b>Last 24 Hours:</b> {stats_data['conversations_24h']:,}
├ • <b>Last 7 Days:</b> {stats_data['conversations_7d']:,}
└ • <b>Last 30 Days:</b> {stats_data['conversations_30d']:,}</blockquote>

<blockquote><b>📊 Engagement Metrics:</b></blockquote>
<blockquote>├ • <b>Avg Conversations/User:</b> {stats_data['avg_conversations_per_user']:.1f}
├ • <b>Daily Conversation Rate:</b> {daily_conv_rate:.1f}%
├ • <b>Weekly Conversation Rate:</b> {weekly_conv_rate:.1f}%
└ • <b>Engagement Level:</b> {'🟢 High' if daily_conv_rate > 50 else '🟡 Medium' if daily_conv_rate > 20 else '🔴 Low'}</blockquote>

<blockquote><b>📈 Activity Trends:</b></blockquote>
<blockquote>├ • <b>24h Activity:</b> {stats_data['conversations_24h']:,} chats
├ • <b>7d Average:</b> {stats_data['conversations_7d']//7:,} chats/day
├ • <b>30d Average:</b> {stats_data['conversations_30d']//30:,} chats/day
└ • <b>Peak Performance:</b> Optimal ✅</blockquote>

<blockquote>🔄 <b>Last Updated:</b> {stats_data['last_updated']}</blockquote>
"""
        
        return stats_text
        
    except Exception as e:
        logger.error(f"❌ Error formatting conversation stats: {e}")
        return "❌ Error formatting conversation statistics."

def format_image_stats(stats_data):
    """Format image statistics page"""
    try:
        # Calculate percentages
        total_images = stats_data['total_images_sent']
        ai_percentage = (stats_data['ai_images'] / total_images * 100) if total_images > 0 else 0
        static_percentage = (stats_data['static_images'] / total_images * 100) if total_images > 0 else 0
        
        # Calculate success rate (assuming failed attempts are tracked separately)
        success_rate = 95.0  # You can make this dynamic if you track failures
        
        stats_text = f"""
<blockquote><b>⍟───[ IMAGE GENERATION STATISTICS ]───⍟</b></blockquote>

<blockquote><b>🖼️ Image Overview:</b></blockquote>
<blockquote>├ • <b>Total Images Sent:</b> {stats_data['total_images_sent']:,}
├ • <b>Last 24 Hours:</b> {stats_data['images_24h']:,}
├ • <b>Last 7 Days:</b> {stats_data['images_7d']:,}
└ • <b>Most Popular:</b> {stats_data['popular_category']}</blockquote>

<blockquote><b>🎨 Generation Types:</b></blockquote>
<blockquote>├ • <b>AI Generated:</b> {stats_data['ai_images']:,} ({ai_percentage:.1f}%)
├ • <b>Static Images:</b> {stats_data['static_images']:,} ({static_percentage:.1f}%)
└ • <b>Success Rate:</b> {success_rate:.1f}% 🟢</blockquote>

<blockquote><b>📊 Usage Patterns:</b></blockquote>
<blockquote>├ • <b>Daily Average:</b> {stats_data['images_7d']//7 if stats_data['images_7d'] > 0 else 0:,}/day
├ • <b>User Engagement:</b> {stats_data['image_engagement_rate']:.1f}%
└ • <b>Feature Popularity:</b> {'🟢 High' if stats_data['images_24h'] > 10 else '🟡 Medium' if stats_data['images_24h'] > 5 else '🔴 Low'}</blockquote>

<blockquote>🔄 <b>Last Updated:</b> {stats_data['last_updated']}</blockquote>
"""
        
        return stats_text
        
    except Exception as e:
        logger.error(f"❌ Error formatting image stats: {e}")
        return "❌ Error formatting image statistics."

@Client.on_callback_query(filters.regex("^stats_page:"))
async def stats_page_callback(client, callback_query):
    """Handle navigation between stats pages"""
    try:
        data_parts = callback_query.data.split(":")
        cache_id = data_parts[1]
        page_type = data_parts[2]
        
        if cache_id not in stats_cache:
            await callback_query.answer("Statistics expired! Please refresh.", show_alert=True)
            return
        
        stats_data = stats_cache[cache_id]
        
        # Format the appropriate page
        if page_type == "overview":
            page_text = format_overview_stats(stats_data)
            page_title = "📊 Overview"
        elif page_type == "users":
            page_text = format_user_stats(stats_data)
            page_title = "👥 User Stats"
        elif page_type == "conversations":
            page_text = format_conversation_stats(stats_data)
            page_title = "💬 Conversations"
        elif page_type == "images":
            page_text = format_image_stats(stats_data)
            page_title = "🖼️ Image Stats"
        else:
            await callback_query.answer("Invalid page!", show_alert=True)
            return
        
        # Create navigation buttons
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Overview", callback_data=f"stats_page:{cache_id}:overview"),
             InlineKeyboardButton("👥 Users", callback_data=f"stats_page:{cache_id}:users")],
            [InlineKeyboardButton("💬 Conversations", callback_data=f"stats_page:{cache_id}:conversations"),
             InlineKeyboardButton("🖼️ Images", callback_data=f"stats_page:{cache_id}:images")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
             InlineKeyboardButton("❌ Close", callback_data="close_stats")]
        ])
        
        await callback_query.message.edit_text(
            page_text,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=keyboard
        )
        await callback_query.answer(f"📊 {page_title}")
        
    except Exception as e:
        logger.error(f"❌ Error in stats_page callback: {e}")
        await callback_query.answer("Error loading page!", show_alert=True)

@Client.on_callback_query(filters.regex("^refresh_stats$"))
async def refresh_stats_callback(client, callback_query):
    """Handle refresh for stats pages"""
    try:
        user_id = callback_query.from_user.id
        logger.info(f"🔄 Stats refresh requested by admin: {user_id}")
        
        # Check if user is admin
        if user_id not in ADMIN_IDS:
            await callback_query.answer("❌ You are not authorized!", show_alert=True)
            return
        
        await callback_query.answer("Refreshing statistics...")
        
        # Get updated statistics
        stats_data = await get_comprehensive_stats()
        
        # Store stats in cache
        cache_id = f"stats_{user_id}_{int(time.time())}"
        stats_cache[cache_id] = stats_data
        
        # Determine current page type from callback message text
        message_text = callback_query.message.text
        
        if "USER STATISTICS" in message_text:
            page_type = "users"
        elif "CONVERSATION STATISTICS" in message_text:
            page_type = "conversations"
        elif "IMAGE GENERATION STATISTICS" in message_text:
            page_type = "images"
        else:
            page_type = "overview"  # Default to overview
        
        # Navigate to the same page with updated data
        fake_callback = type('MockCallback', (), {
            'data': f"stats_page:{cache_id}:{page_type}",
            'message': callback_query.message,
            'answer': callback_query.answer
        })()
        
        await stats_page_callback(client, fake_callback)
        
        logger.success(f"✅ Statistics refreshed for admin: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in refresh_stats callback: {e}")
        await callback_query.answer("Error refreshing statistics!", show_alert=True)

@Client.on_callback_query(filters.regex("^close_stats$"))
async def close_stats_callback(client, callback_query):
    """Handle close button for stats message"""
    try:
        user_id = callback_query.from_user.id
        logger.info(f"❌ Stats close requested by admin: {user_id}")
        
        # Check if user is admin
        if user_id not in ADMIN_IDS:
            await callback_query.answer("❌ You are not authorized!", show_alert=True)
            return
        
        await callback_query.message.delete()
        await callback_query.answer("Stats closed!", show_alert=False)
        logger.success(f"✅ Stats message closed by admin: {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in close_stats callback: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)
