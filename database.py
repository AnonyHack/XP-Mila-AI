import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pymongo import MongoClient
from config import MONGO_DB_URI, MONGO_DB_NAME

logger = logging.getLogger(__name__)

class BotDatabase:
    def __init__(self):
        try:
            self.client = MongoClient(MONGO_DB_URI)
            self.db = self.client[MONGO_DB_NAME]
            self.users_collection = self.db["users"]
            self.conversations_collection = self.db["conversations"]
            self.conversation_stats = self.db["conversation_stats"]  # New collection for persistent stats
            logger.info("MongoDB initialized")
        except Exception as e:
            logger.error(f"MongoDB error: {e}")
            raise

    def add_user(self, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None):
        try:
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "is_verified": False,
                "joined_at": datetime.now(),
                "preferences": {}  # Store girlfriend-specific preferences
            }
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$setOnInsert": user_data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False

    def update_preferences(self, user_id: int, preferences: dict):
        try:
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"preferences": preferences}}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return False

    def get_preferences(self, user_id: int) -> dict:
        try:
            user = self.users_collection.find_one({"user_id": user_id})
            return user.get("preferences", {}) if user else {}
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return {}

    def verify_user(self, user_id: int):
        try:
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"is_verified": True}}
            )
            return True
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            return False

    def is_user_verified(self, user_id: int) -> bool:
        try:
            user = self.users_collection.find_one({"user_id": user_id})
            return bool(user and user.get("is_verified", False))
        except Exception as e:
            logger.error(f"Error checking verification: {e}")
            return False

    def get_all_users(self) -> List[int]:
        try:
            users = self.users_collection.find({"is_verified": True})
            return [user["user_id"] for user in users]
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []

    def get_active_users_7d(self) -> int:
        try:
            seven_days_ago = datetime.now() - timedelta(days=7)
            pipeline = [
                {"$match": {"timestamp": {"$gte": seven_days_ago}}},
                {"$group": {"_id": "$user_id"}},
                {"$count": "active_users"}
            ]
            result = list(self.conversations_collection.aggregate(pipeline))
            return result[0]["active_users"] if result else 0
        except Exception as e:
            logger.error(f"Error getting active users (7d): {e}")
            return 0

    def get_new_users_24h(self) -> int:
        try:
            one_day_ago = datetime.now() - timedelta(hours=24)
            return self.users_collection.count_documents({
                "is_verified": True,
                "joined_at": {"$gte": one_day_ago}
            })
        except Exception as e:
            logger.error(f"Error getting new users (24h): {e}")
            return 0

    def get_conversation_counts(self) -> dict:
        try:
            now = datetime.now()
            one_day_ago = now - timedelta(hours=24)
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            
            pipeline = [
                {"$match": {"timestamp": {"$gte": thirty_days_ago}}},
                {"$group": {
                    "_id": None,
                    "total_24h": {
                        "$sum": {
                            "$cond": [
                                {"$gte": ["$timestamp", one_day_ago]},
                                1,
                                0
                            ]
                        }
                    },
                    "total_7d": {
                        "$sum": {
                            "$cond": [
                                {"$gte": ["$timestamp", seven_days_ago]},
                                1,
                                0
                            ]
                        }
                    },
                    "total_30d": {"$sum": 1}
                }}
            ]
            result = list(self.conversations_collection.aggregate(pipeline))
            counts = result[0] if result else {"total_24h": 0, "total_7d": 0, "total_30d": 0}
            return {
                "24h": counts.get("total_24h", 0),
                "7d": counts.get("total_7d", 0),
                "30d": counts.get("total_30d", 0)
            }
        except Exception as e:
            logger.error(f"Error getting conversation counts: {e}")
            return {"24h": 0, "7d": 0, "30d": 0}

    def add_conversation(self, user_id: int, role: str, content: str):
        try:
            # Add to conversations_collection
            conversation_data = {
                "user_id": user_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now()
            }
            self.conversations_collection.insert_one(conversation_data)
            
            # Increment persistent conversation stats
            self.conversation_stats.update_one(
                {"key": "total_conversations"},
                {
                    "$inc": {
                        "total": 1,
                        "last_24h": 1,
                        "last_7d": 1,
                        "last_30d": 1
                    },
                    "$set": {"updated_at": datetime.now()}
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error adding conversation: {e}")
            return False

    def get_persistent_conversation_counts(self) -> dict:
        try:
            now = datetime.now()
            one_day_ago = now - timedelta(hours=24)
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            
            # Reset expired counts
            self.conversation_stats.update_one(
                {"key": "total_conversations"},
                {
                    "$set": {
                        "last_24h": 0 if self.conversation_stats.find_one({"key": "total_conversations", "updated_at": {"$lt": one_day_ago}}) else self.conversation_stats.find_one({"key": "total_conversations"})["last_24h"],
                        "last_7d": 0 if self.conversation_stats.find_one({"key": "total_conversations", "updated_at": {"$lt": seven_days_ago}}) else self.conversation_stats.find_one({"key": "total_conversations"})["last_7d"],
                        "last_30d": 0 if self.conversation_stats.find_one({"key": "total_conversations", "updated_at": {"$lt": thirty_days_ago}}) else self.conversation_stats.find_one({"key": "total_conversations"})["last_30d"],
                    }
                },
                upsert=True
            )
            
            stats = self.conversation_stats.find_one({"key": "total_conversations"})
            return {
                "total": stats.get("total", 0) if stats else 0,
                "24h": stats.get("last_24h", 0) if stats else 0,
                "7d": stats.get("last_7d", 0) if stats else 0,
                "30d": stats.get("last_30d", 0) if stats else 0
            }
        except Exception as e:
            logger.error(f"Error getting persistent conversation counts: {e}")
            return {"total": 0, "24h": 0, "7d": 0, "30d": 0}

    def get_conversation_history(self, user_id: int, limit: int = 10) -> List[dict]:
        try:
            conversations = self.conversations_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
            return [{"role": conv["role"], "content": conv["content"]} for conv in reversed(list(conversations))]
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    def clear_conversation(self, user_id: int):
        try:
            self.conversations_collection.delete_many({"user_id": user_id})
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
