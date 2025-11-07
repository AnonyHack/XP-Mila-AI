import asyncio
import random
from datetime import datetime, timedelta
from loguru import logger
from pyrogram import Client
from database import BotDatabase
from config import (
    REMINDER_ENABLED, 
    REMINDER_CHECK_INTERVAL,
    REMINDER_INACTIVITY_THRESHOLD,
    REMINDER_DELETE_AFTER,
    REMINDER_MESSAGES
)

db = BotDatabase()

class ReminderSystem:
    def __init__(self, client: Client):
        self.client = client
        self.is_running = False
        self.task = None

    async def start(self):
        """Start the reminder system"""
        if not REMINDER_ENABLED:
            logger.info("⏰ Reminder system is disabled")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._reminder_loop())
        logger.info("⏰ Reminder system started")

    async def stop(self):
        """Stop the reminder system"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("⏰ Reminder system stopped")

    async def _reminder_loop(self):
        """Main reminder loop"""
        while self.is_running:
            try:
                await self._check_and_send_reminders()
                await asyncio.sleep(REMINDER_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"⏰ Error in reminder loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def _check_and_send_reminders(self):
        """Check for inactive users and send reminders"""
        try:
            logger.info("⏰ Checking for inactive users...")
            
            # Get users who are eligible for reminders
            users = db.get_users_for_reminders(REMINDER_INACTIVITY_THRESHOLD)
            
            if not users:
                logger.info("⏰ No users need reminders right now")
                return

            logger.info(f"⏰ Found {len(users)} users eligible for reminders")
            
            for user in users:
                await self._send_reminder_to_user(user)
                await asyncio.sleep(2)  # Small delay between sends to avoid rate limits
            
            # Clean up old reminders
            await self._cleanup_old_reminders()
            
        except Exception as e:
            logger.error(f"⏰ Error checking reminders: {e}")

    async def _send_reminder_to_user(self, user: dict):
        """Send a reminder to a specific user"""
        try:
            user_id = user["user_id"]
            first_name = user.get("first_name", "darling")
            
            # Select a random reminder message
            reminder_data = random.choice(REMINDER_MESSAGES)
            message_text = reminder_data["text"].format(first_name=first_name)
            image_url = reminder_data.get("image")
            
            logger.info(f"⏰ Sending reminder to user {user_id} ({first_name})")
            
            if image_url:
                # Send reminder with image
                message = await self.client.send_photo(
                    chat_id=user_id,
                    photo=image_url,
                    caption=message_text
                )
            else:
                # Send reminder as text only
                message = await self.client.send_message(
                    chat_id=user_id,
                    text=message_text
                )
            
            # Track the sent reminder
            db.add_reminder_sent(user_id, message.id, reminder_data)
            logger.success(f"⏰ Reminder sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"⏰ Failed to send reminder to user {user_id}: {e}")

    async def _cleanup_old_reminders(self):
        """Delete old reminders that haven't been responded to"""
        try:
            reminders_to_delete = db.get_pending_reminders_to_delete()
            
            if not reminders_to_delete:
                return
            
            logger.info(f"⏰ Cleaning up {len(reminders_to_delete)} old reminders")
            
            deleted_count = 0
            for reminder in reminders_to_delete:
                success = await self._delete_reminder_message(reminder)
                if success:
                    deleted_count += 1
                await asyncio.sleep(1)  # Small delay between deletions
            
            logger.success(f"⏰ Successfully cleaned up {deleted_count} old reminders")
            
        except Exception as e:
            logger.error(f"⏰ Error cleaning up reminders: {e}")

    async def _delete_reminder_message(self, reminder: dict):
        """Delete a reminder message and mark it as deleted"""
        try:
            user_id = reminder["user_id"]
            message_id = reminder["message_id"]
            
            # Try to delete the message
            await self.client.delete_messages(
                chat_id=user_id,
                message_ids=message_id
            )
            
            # Mark as deleted in database
            db.mark_reminder_deleted(user_id, message_id)
            logger.info(f"⏰ Deleted old reminder for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"⏰ Failed to delete reminder for user {reminder['user_id']}: {e}")
            # Mark as deleted anyway to avoid repeated attempts
            db.mark_reminder_deleted(reminder['user_id'], reminder['message_id'])
            return False

    async def handle_user_response(self, user_id: int):
        """Handle when a user responds to a reminder"""
        try:
            # Update user's last activity
            db.update_user_last_activity(user_id)
            
            # Mark any pending reminders as responded
            recent_reminder = db.get_user_recent_reminder(user_id)
            if recent_reminder and not recent_reminder.get("responded", False):
                db.mark_reminder_responded(user_id, recent_reminder["message_id"])
                logger.info(f"⏰ User {user_id} responded to reminder")
            
        except Exception as e:
            logger.error(f"⏰ Error handling user response: {e}")

# Global instance
reminder_system = None

async def initialize_reminder_system(client: Client):
    """Initialize the reminder system"""
    global reminder_system
    reminder_system = ReminderSystem(client)
    await reminder_system.start()
    return reminder_system

async def shutdown_reminder_system():
    """Shutdown the reminder system"""
    global reminder_system
    if reminder_system:
        await reminder_system.stop()