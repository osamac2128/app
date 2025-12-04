"""Pass repository for hall pass database operations"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository
from datetime import datetime, timedelta
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class PassRepository(BaseRepository):
    """Repository for passes collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "passes")

    async def find_active_pass_by_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an active pass for a student.

        Args:
            student_id: Student user ID

        Returns:
            Active pass document or None
        """
        return await self.find_one({
            "student_id": student_id,
            "status": "active"
        })

    async def find_pending_pass_by_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a pending pass for a student.

        Args:
            student_id: Student user ID

        Returns:
            Pending pass document or None
        """
        return await self.find_one({
            "student_id": student_id,
            "status": "pending"
        })

    async def has_active_or_pending_pass(self, student_id: str) -> bool:
        """
        Check if student has an active or pending pass.

        Args:
            student_id: Student user ID

        Returns:
            True if student has active or pending pass
        """
        return await self.exists({
            "student_id": student_id,
            "status": {"$in": ["active", "pending", "approved"]}
        })

    async def find_all_active_passes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find all currently active passes (for hall monitor view).

        Args:
            limit: Maximum number of passes to return

        Returns:
            List of active pass documents
        """
        return await self.find_many(
            {"status": "active"},
            limit=limit,
            sort=[("departed_at", -1)]
        )

    async def find_passes_by_student(
        self,
        student_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find all passes for a student (history).

        Args:
            student_id: Student user ID
            limit: Maximum number of passes to return

        Returns:
            List of pass documents sorted by most recent
        """
        return await self.find_many(
            {"student_id": student_id},
            limit=limit,
            sort=[("requested_at", -1)]
        )

    async def find_passes_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Find passes within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of passes to return

        Returns:
            List of pass documents
        """
        return await self.find_many(
            {
                "requested_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            },
            limit=limit,
            sort=[("requested_at", -1)]
        )

    async def count_daily_passes_for_student(
        self,
        student_id: str,
        date: datetime = None
    ) -> int:
        """
        Count passes created by student on a specific date.

        Args:
            student_id: Student user ID
            date: Date to check (default: today)

        Returns:
            Number of passes created on the date
        """
        if date is None:
            date = datetime.utcnow()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return await self.count({
            "student_id": student_id,
            "requested_at": {
                "$gte": start_of_day,
                "$lt": end_of_day
            }
        })

    async def find_overtime_passes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find all passes that are currently overtime.

        Args:
            limit: Maximum number of passes to return

        Returns:
            List of overtime pass documents
        """
        return await self.find_many(
            {
                "status": "active",
                "is_overtime": True
            },
            limit=limit,
            sort=[("departed_at", 1)]
        )

    async def mark_pass_overtime(self, pass_id: str) -> bool:
        """
        Mark a pass as overtime.

        Args:
            pass_id: Pass ID

        Returns:
            True if updated successfully
        """
        return await self.update_one(pass_id, {"is_overtime": True})

    async def end_pass(self, pass_id: str) -> bool:
        """
        End a pass (mark as completed).

        Args:
            pass_id: Pass ID

        Returns:
            True if ended successfully
        """
        return await self.update_one(pass_id, {
            "status": "completed",
            "returned_at": datetime.utcnow()
        })

    async def approve_pass(self, pass_id: str, approved_by: str) -> bool:
        """
        Approve a pending pass.

        Args:
            pass_id: Pass ID
            approved_by: User ID of approver

        Returns:
            True if approved successfully
        """
        return await self.update_one(pass_id, {
            "status": "approved",
            "approved_by": approved_by,
            "approved_at": datetime.utcnow()
        })

    async def deny_pass(self, pass_id: str, denied_by: str, reason: str = None) -> bool:
        """
        Deny a pending pass.

        Args:
            pass_id: Pass ID
            denied_by: User ID of denier
            reason: Optional reason for denial

        Returns:
            True if denied successfully
        """
        update_data = {
            "status": "denied",
            "denied_by": denied_by,
            "denied_at": datetime.utcnow()
        }
        if reason:
            update_data["denial_reason"] = reason

        return await self.update_one(pass_id, update_data)


class LocationRepository(BaseRepository):
    """Repository for locations collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "locations")

    async def find_active_locations(self) -> List[Dict[str, Any]]:
        """
        Find all active locations.

        Returns:
            List of active location documents
        """
        return await self.find_many({"is_active": True}, limit=200)

    async def find_by_type(self, location_type: str) -> List[Dict[str, Any]]:
        """
        Find locations by type.

        Args:
            location_type: Location type (office, library, etc.)

        Returns:
            List of location documents
        """
        return await self.find_many({
            "type": location_type,
            "is_active": True
        })

    async def count_active_passes_for_location(self, location_id: str) -> int:
        """
        Count active passes going to a specific location.

        Args:
            location_id: Location ID

        Returns:
            Number of active passes to this location
        """
        # Access the passes collection through the db instance
        passes_collection = self.db["passes"]
        return await passes_collection.count_documents({
            "destination_location_id": location_id,
            "status": "active"
        })

    async def is_location_at_capacity(self, location_id: str) -> bool:
        """
        Check if a location is at max capacity.

        Args:
            location_id: Location ID

        Returns:
            True if at capacity, False otherwise
        """
        location = await self.find_by_id(location_id)
        if not location or location.get("max_capacity") is None:
            return False

        active_count = await self.count_active_passes_for_location(location_id)
        return active_count >= location["max_capacity"]
