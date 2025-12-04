"""Notification repository for notification database operations"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationRepository(BaseRepository):
    """Repository for notifications collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "notifications")

    async def find_pending_notifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find notifications pending to be sent.

        Args:
            limit: Maximum number of notifications to return

        Returns:
            List of pending notification documents
        """
        return await self.find_many(
            {
                "status": "pending",
                "scheduled_at": {"$lte": datetime.utcnow()}
            },
            limit=limit,
            sort=[("scheduled_at", 1)]
        )

    async def find_sent_notifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find sent notifications.

        Args:
            limit: Maximum number of notifications to return

        Returns:
            List of sent notification documents
        """
        return await self.find_many(
            {"status": "sent"},
            limit=limit,
            sort=[("sent_at", -1)]
        )

    async def find_notifications_by_creator(
        self,
        created_by: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find notifications created by a specific user.

        Args:
            created_by: Creator user ID
            limit: Maximum number of notifications to return

        Returns:
            List of notification documents
        """
        return await self.find_many(
            {"created_by": created_by},
            limit=limit,
            sort=[("created_at", -1)]
        )

    async def mark_as_sent(self, notification_id: str) -> bool:
        """
        Mark notification as sent.

        Args:
            notification_id: Notification ID

        Returns:
            True if updated successfully
        """
        return await self.update_one(notification_id, {
            "status": "sent",
            "sent_at": datetime.utcnow()
        })

    async def mark_as_failed(self, notification_id: str, error: str) -> bool:
        """
        Mark notification as failed.

        Args:
            notification_id: Notification ID
            error: Error message

        Returns:
            True if updated successfully
        """
        return await self.update_one(notification_id, {
            "status": "failed",
            "error_message": error,
            "failed_at": datetime.utcnow()
        })


class NotificationReceiptRepository(BaseRepository):
    """Repository for notification_receipts collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "notification_receipts")

    async def find_receipts_by_notification(
        self,
        notification_id: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Find all receipts for a notification.

        Args:
            notification_id: Notification ID
            limit: Maximum number of receipts to return

        Returns:
            List of receipt documents
        """
        return await self.find_many(
            {"notification_id": notification_id},
            limit=limit
        )

    async def find_receipts_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find all receipts for a user.

        Args:
            user_id: User ID
            limit: Maximum number of receipts to return

        Returns:
            List of receipt documents
        """
        return await self.find_many(
            {"user_id": user_id},
            limit=limit,
            sort=[("delivered_at", -1)]
        )

    async def find_unread_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Find unread notifications for a user.

        Args:
            user_id: User ID

        Returns:
            List of unread receipt documents
        """
        return await self.find_many(
            {
                "user_id": user_id,
                "read_at": None
            },
            limit=100,
            sort=[("delivered_at", -1)]
        )

    async def mark_as_read(self, receipt_id: str) -> bool:
        """
        Mark receipt as read.

        Args:
            receipt_id: Receipt ID

        Returns:
            True if updated successfully
        """
        return await self.update_one(receipt_id, {
            "read_at": datetime.utcnow()
        })

    async def mark_all_as_read_for_user(self, user_id: str) -> int:
        """
        Mark all receipts as read for a user.

        Args:
            user_id: User ID

        Returns:
            Number of receipts marked as read
        """
        return await self.update_many(
            {
                "user_id": user_id,
                "read_at": None
            },
            {"read_at": datetime.utcnow()}
        )

    async def count_unread_for_user(self, user_id: str) -> int:
        """
        Count unread notifications for a user.

        Args:
            user_id: User ID

        Returns:
            Number of unread notifications
        """
        return await self.count({
            "user_id": user_id,
            "read_at": None
        })

    async def get_delivery_stats(self, notification_id: str) -> Dict[str, int]:
        """
        Get delivery statistics for a notification.

        Args:
            notification_id: Notification ID

        Returns:
            Dict with delivered, read, failed counts
        """
        total = await self.count({"notification_id": notification_id})
        delivered = await self.count({
            "notification_id": notification_id,
            "delivery_status": "delivered"
        })
        read = await self.count({
            "notification_id": notification_id,
            "read_at": {"$ne": None}
        })
        failed = await self.count({
            "notification_id": notification_id,
            "delivery_status": "failed"
        })

        return {
            "total": total,
            "delivered": delivered,
            "read": read,
            "failed": failed,
            "delivery_rate": round((delivered / total * 100) if total > 0 else 0, 2),
            "read_rate": round((read / delivered * 100) if delivered > 0 else 0, 2)
        }


class NotificationTemplateRepository(BaseRepository):
    """Repository for notification_templates collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "notification_templates")

    async def find_active_templates(self) -> List[Dict[str, Any]]:
        """
        Find all active notification templates.

        Returns:
            List of active template documents
        """
        return await self.find_many({"is_active": True}, limit=100)

    async def find_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Find templates by category.

        Args:
            category: Template category

        Returns:
            List of template documents
        """
        return await self.find_many({
            "category": category,
            "is_active": True
        }, limit=50)

    async def deactivate_template(self, template_id: str) -> bool:
        """
        Deactivate a template.

        Args:
            template_id: Template ID

        Returns:
            True if deactivated successfully
        """
        return await self.update_one(template_id, {"is_active": False})
