"""User repository for user-specific database operations"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "users")

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find a user by email address.

        Args:
            email: User's email address

        Returns:
            User document or None if not found
        """
        return await self.find_one({"email": email.lower()})

    async def find_by_role(self, role: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find users by role.

        Args:
            role: User role (student, parent, staff, admin)
            limit: Maximum number of users to return

        Returns:
            List of user documents
        """
        return await self.find_many({"role": role}, limit=limit)

    async def find_active_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find all active users.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of active user documents
        """
        return await self.find_many({"status": "active"}, limit=limit)

    async def email_exists(self, email: str) -> bool:
        """
        Check if an email address is already registered.

        Args:
            email: Email address to check

        Returns:
            True if email exists, False otherwise
        """
        return await self.exists({"email": email.lower()})

    async def update_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            True if updated successfully
        """
        from datetime import datetime
        return await self.update_one(user_id, {"last_login_at": datetime.utcnow()})

    async def update_device_token(self, user_id: str, device_token: str) -> bool:
        """
        Add or update a device token for push notifications.

        Args:
            user_id: User ID
            device_token: Device token for push notifications

        Returns:
            True if updated successfully
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$addToSet": {"device_tokens": device_token}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating device token for user {user_id}: {e}")
            return False

    async def remove_device_token(self, user_id: str, device_token: str) -> bool:
        """
        Remove a device token.

        Args:
            user_id: User ID
            device_token: Device token to remove

        Returns:
            True if removed successfully
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$pull": {"device_tokens": device_token}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error removing device token for user {user_id}: {e}")
            return False

    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            True if deactivated successfully
        """
        return await self.update_one(user_id, {"status": "inactive"})

    async def activate_user(self, user_id: str) -> bool:
        """
        Activate a user account.

        Args:
            user_id: User ID

        Returns:
            True if activated successfully
        """
        return await self.update_one(user_id, {"status": "active"})
