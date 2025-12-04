"""Emergency repository for emergency alert database operations"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository
from datetime import datetime
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class EmergencyAlertRepository(BaseRepository):
    """Repository for emergency_alerts collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "emergency_alerts")

    async def find_active_alert(self) -> Optional[Dict[str, Any]]:
        """
        Find the currently active emergency alert.

        Returns:
            Active emergency alert document or None
        """
        return await self.find_one({
            "resolved_at": None,
            "is_drill": False
        })

    async def find_active_drill(self) -> Optional[Dict[str, Any]]:
        """
        Find the currently active drill.

        Returns:
            Active drill document or None
        """
        return await self.find_one({
            "resolved_at": None,
            "is_drill": True
        })

    async def find_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Find recent emergency alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alert documents
        """
        return await self.find_many(
            {},
            limit=limit,
            sort=[("triggered_at", -1)]
        )

    async def find_alerts_by_type(
        self,
        alert_type: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find alerts by type.

        Args:
            alert_type: Alert type (lockdown, evacuation, etc.)
            limit: Maximum number of alerts to return

        Returns:
            List of alert documents
        """
        return await self.find_many(
            {"type": alert_type},
            limit=limit,
            sort=[("triggered_at", -1)]
        )

    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: str = None
    ) -> bool:
        """
        Resolve an active alert.

        Args:
            alert_id: Alert ID
            resolved_by: User ID who resolved the alert
            resolution_notes: Optional resolution notes

        Returns:
            True if resolved successfully
        """
        update_data = {
            "resolved_at": datetime.utcnow(),
            "resolved_by": resolved_by
        }
        if resolution_notes:
            update_data["resolution_notes"] = resolution_notes

        return await self.update_one(alert_id, update_data)

    async def has_active_alert(self) -> bool:
        """
        Check if there is an active alert (non-drill).

        Returns:
            True if active alert exists
        """
        return await self.exists({
            "resolved_at": None,
            "is_drill": False
        })


class EmergencyCheckInRepository(BaseRepository):
    """Repository for emergency_check_ins collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "emergency_check_ins")

    async def find_check_ins_by_alert(
        self,
        alert_id: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Find all check-ins for an alert.

        Args:
            alert_id: Alert ID
            limit: Maximum number of check-ins to return

        Returns:
            List of check-in documents
        """
        return await self.find_many(
            {"alert_id": alert_id},
            limit=limit,
            sort=[("checked_in_at", -1)]
        )

    async def find_check_in_by_user_and_alert(
        self,
        alert_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find check-in for specific user and alert.

        Args:
            alert_id: Alert ID
            user_id: User ID

        Returns:
            Check-in document or None
        """
        return await self.find_one({
            "alert_id": alert_id,
            "user_id": user_id
        })

    async def count_checked_in_by_alert(self, alert_id: str) -> int:
        """
        Count users who have checked in for an alert.

        Args:
            alert_id: Alert ID

        Returns:
            Number of users checked in
        """
        return await self.count({
            "alert_id": alert_id,
            "status": "safe"
        })

    async def count_not_checked_in_by_alert(self, alert_id: str) -> int:
        """
        Count users who have not checked in for an alert.

        Args:
            alert_id: Alert ID

        Returns:
            Number of users not checked in
        """
        return await self.count({
            "alert_id": alert_id,
            "status": "pending"
        })

    async def check_in_user(
        self,
        alert_id: str,
        user_id: str,
        location: str = None,
        notes: str = None
    ) -> str:
        """
        Create or update check-in for user.

        Args:
            alert_id: Alert ID
            user_id: User ID
            location: Optional current location
            notes: Optional check-in notes

        Returns:
            Check-in ID
        """
        # Check if check-in already exists
        existing = await self.find_check_in_by_user_and_alert(alert_id, user_id)

        if existing:
            # Update existing check-in
            await self.update_one(existing["_id"], {
                "status": "safe",
                "location": location,
                "notes": notes,
                "checked_in_at": datetime.utcnow()
            })
            return existing["_id"]
        else:
            # Create new check-in
            check_in_data = {
                "alert_id": alert_id,
                "user_id": user_id,
                "status": "safe",
                "location": location,
                "notes": notes,
                "checked_in_at": datetime.utcnow()
            }
            return await self.insert_one(check_in_data)

    async def get_check_in_stats(self, alert_id: str) -> Dict[str, int]:
        """
        Get check-in statistics for an alert.

        Args:
            alert_id: Alert ID

        Returns:
            Dict with total, checked_in, not_checked_in counts
        """
        total = await self.count({"alert_id": alert_id})
        checked_in = await self.count_checked_in_by_alert(alert_id)
        not_checked_in = await self.count_not_checked_in_by_alert(alert_id)

        return {
            "total": total,
            "checked_in": checked_in,
            "not_checked_in": not_checked_in,
            "percentage": round((checked_in / total * 100) if total > 0 else 0, 2)
        }
