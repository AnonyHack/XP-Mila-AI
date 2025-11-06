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
            self.conversation_stats = self.db["conversation_stats"]
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
                "preferences": {} 
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
            conversation_data = {
                "user_id": user_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now()
            }
            self.conversations_collection.insert_one(conversation_data)
            
            # Increment persistent conversation stats
            now = datetime.now()
            self.conversation_stats.update_one(
                {"key": "total_conversations"},
                {"$inc": {"total": 1}},
                upsert=True
            )
            self.conversation_stats.update_one(
                {"key": f"conv_{now.year}_{now.month}_{now.day}"},
                {"$inc": {"count": 1}},
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
            
            # Total conversations
            total_stats = self.conversation_stats.find_one({"key": "total_conversations"})
            total = total_stats.get("total", 0) if total_stats else 0
            
            # Time-based counts via aggregation on daily keys
            pipeline_24h = [
                {"$match": {"key": {"$regex": f"^conv_{now.year}_.*$"}}},
                {"$project": {"date": {"$dateFromString": {"dateString": {"$substr": ["$key", 5, 10]}, "format": "%Y_%m_%d"}}}},
                {"$match": {"date": {"$gte": one_day_ago}}},
                {"$group": {"_id": None, "count": {"$sum": "$count"}}}
            ]
            result_24h = list(self.conversation_stats.aggregate(pipeline_24h))
            count_24h = result_24h[0]["count"] if result_24h else 0
            
            pipeline_7d = [
                {"$match": {"key": {"$regex": f"^conv_{now.year}_.*$"}}},
                {"$project": {"date": {"$dateFromString": {"dateString": {"$substr": ["$key", 5, 10]}, "format": "%Y_%m_%d"}}}},
                {"$match": {"date": {"$gte": seven_days_ago}}},
                {"$group": {"_id": None, "count": {"$sum": "$count"}}}
            ]
            result_7d = list(self.conversation_stats.aggregate(pipeline_7d))
            count_7d = result_7d[0]["count"] if result_7d else 0
            
            pipeline_30d = [
                {"$match": {"key": {"$regex": f"^conv_{now.year}_.*$"}}},
                {"$project": {"date": {"$dateFromString": {"dateString": {"$substr": ["$key", 5, 10]}, "format": "%Y_%m_%d"}}}},
                {"$match": {"date": {"$gte": thirty_days_ago}}},
                {"$group": {"_id": None, "count": {"$sum": "$count"}}}
            ]
            result_30d = list(self.conversation_stats.aggregate(pipeline_30d))
            count_30d = result_30d[0]["count"] if result_30d else 0
            
            return {
                "total": total,
                "24h": count_24h,
                "7d": count_7d,
                "30d": count_30d
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

    def add_image_generation(self, user_id: int, category: str, image_type: str, success: bool = True):
        """Track image generation attempts"""
        try:
            image_data = {
                "user_id": user_id,
                "category": category,
                "image_type": image_type,  # 'ai_generated' or 'static'
                "success": success,
                "timestamp": datetime.now()
            }
            self.db["image_generations"].insert_one(image_data)
            
            # Update persistent image stats
            now = datetime.now()
            self.conversation_stats.update_one(
                {"key": "total_images"},
                {"$inc": {"total": 1}},
                upsert=True
            )
            
            # Track by type
            self.conversation_stats.update_one(
                {"key": f"images_{image_type}"},
                {"$inc": {"count": 1}},
                upsert=True
            )
            
            # Track by category
            self.conversation_stats.update_one(
                {"key": f"category_{category}"},
                {"$inc": {"count": 1}},
                upsert=True
            )
            
            # Daily tracking
            self.conversation_stats.update_one(
                {"key": f"img_{now.year}_{now.month}_{now.day}"},
                {"$inc": {"count": 1}},
                upsert=True
            )
            
            return True
        except Exception as e:
            logger.error(f"Error adding image generation: {e}")
            return False

    def get_image_generation_stats(self):
        """Get comprehensive image generation statistics"""
        try:
            now = datetime.now()
            one_day_ago = now - timedelta(hours=24)
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            
            # Total images
            total_stats = self.conversation_stats.find_one({"key": "total_images"})
            total = total_stats.get("total", 0) if total_stats else 0
            
            # AI vs Static images
            ai_stats = self.conversation_stats.find_one({"key": "images_ai_generated"})
            static_stats = self.conversation_stats.find_one({"key": "images_static"})
            
            ai_count = ai_stats.get("count", 0) if ai_stats else 0
            static_count = static_stats.get("count", 0) if static_stats else 0
            
            # Time-based counts via aggregation
            pipeline_24h = [
                {"$match": {"key": {"$regex": f"^img_{now.year}_.*$"}}},
                {"$project": {"date": {"$dateFromString": {"dateString": {"$substr": ["$key", 4, 10]}, "format": "%Y_%m_%d"}}}},
                {"$match": {"date": {"$gte": one_day_ago}}},
                {"$group": {"_id": None, "count": {"$sum": "$count"}}}
            ]
            result_24h = list(self.conversation_stats.aggregate(pipeline_24h))
            count_24h = result_24h[0]["count"] if result_24h else 0
            
            pipeline_7d = [
                {"$match": {"key": {"$regex": f"^img_{now.year}_.*$"}}},
                {"$project": {"date": {"$dateFromString": {"dateString": {"$substr": ["$key", 4, 10]}, "format": "%Y_%m_%d"}}}},
                {"$match": {"date": {"$gte": seven_days_ago}}},
                {"$group": {"_id": None, "count": {"$sum": "$count"}}}
            ]
            result_7d = list(self.conversation_stats.aggregate(pipeline_7d))
            count_7d = result_7d[0]["count"] if result_7d else 0
            
            # Get popular category
            popular_category = self.get_popular_image_category()
            
            return {
                'total': total,
                '24h': count_24h,
                '7d': count_7d,
                'ai_generated': ai_count,
                'static': static_count,
                'popular_category': popular_category
            }
        except Exception as e:
            logger.error(f"Error getting image stats: {e}")
            return {'total': 0, '24h': 0, '7d': 0, 'ai_generated': 0, 'static': 0, 'popular_category': 'None'}

    def get_popular_image_category(self):
        """Get the most popular image category"""
        try:
            # Get all category keys
            category_stats = self.conversation_stats.find({"key": {"$regex": "^category_"}})
            
            popular_category = "None"
            max_count = 0
            
            for stat in category_stats:
                category_name = stat["key"].replace("category_", "")
                count = stat.get("count", 0)
                if count > max_count:
                    max_count = count
                    popular_category = category_name.capitalize()
            
            return popular_category
        except Exception as e:
            logger.error(f"Error getting popular category: {e}")
            return "None"
