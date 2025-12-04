"""Visitor repository for visitor management database operations"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class VisitorRepository(BaseRepository):
    """Repository for visitors collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "visitors")

    async def find_by_id_number(self, id_number: str) -> Optional[Dict[str, Any]]:
        """
        Find visitor by ID number.

        Args:
            id_number: Government ID number

        Returns:
            Visitor document or None
        """
        return await self.find_one({"id_number": id_number})

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find visitor by email.

        Args:
            email: Visitor email

        Returns:
            Visitor document or None
        """
        return await self.find_one({"email": email.lower()})

    async def find_watchlist_visitors(self) -> List[Dict[str, Any]]:
        """
        Find all visitors on watchlist.

        Returns:
            List of watchlist visitor documents
        """
        return await self.find_many({"is_on_watchlist": True}, limit=500)

    async def is_on_watchlist(self, visitor_id: str) -> bool:
        """
        Check if visitor is on watchlist.

        Args:
            visitor_id: Visitor ID

        Returns:
            True if on watchlist
        """
        visitor = await self.find_by_id(visitor_id)
        return visitor.get("is_on_watchlist", False) if visitor else False

    async def add_to_watchlist(self, visitor_id: str, reason: str) -> bool:
        """
        Add visitor to watchlist.

        Args:
            visitor_id: Visitor ID
            reason: Watchlist reason

        Returns:
            True if added successfully
        """
        return await self.update_one(visitor_id, {
            "is_on_watchlist": True,
            "watchlist_reason": reason,
            "watchlist_added_at": datetime.utcnow()
        })

    async def remove_from_watchlist(self, visitor_id: str) -> bool:
        """
        Remove visitor from watchlist.

        Args:
            visitor_id: Visitor ID

        Returns:
            True if removed successfully
        """
        return await self.update_one(visitor_id, {
            "is_on_watchlist": False,
            "watchlist_reason": None
        })


class VisitorLogRepository(BaseRepository):
    """Repository for visitor_logs collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "visitor_logs")

    async def find_active_visits(self) -> List[Dict[str, Any]]:
        """
        Find all active visitor visits (not checked out).

        Returns:
            List of active visit log documents
        """
        return await self.find_many(
            {"checked_out_at": None},
            limit=200,
            sort=[("checked_in_at", -1)]
        )

    async def find_visits_by_visitor(
        self,
        visitor_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find visit history for a visitor.

        Args:
            visitor_id: Visitor ID
            limit: Maximum number of visits to return

        Returns:
            List of visit log documents
        """
        return await self.find_many(
            {"visitor_id": visitor_id},
            limit=limit,
            sort=[("checked_in_at", -1)]
        )

    async def find_visits_by_host(
        self,
        host_user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find visits hosted by a user.

        Args:
            host_user_id: Host user ID
            limit: Maximum number of visits to return

        Returns:
            List of visit log documents
        """
        return await self.find_many(
            {"host_user_id": host_user_id},
            limit=limit,
            sort=[("checked_in_at", -1)]
        )

    async def find_visits_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Find visits within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of visits to return

        Returns:
            List of visit log documents
        """
        return await self.find_many(
            {
                "checked_in_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            },
            limit=limit,
            sort=[("checked_in_at", -1)]
        )

    async def find_active_visit_for_visitor(
        self,
        visitor_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find active visit for a visitor.

        Args:
            visitor_id: Visitor ID

        Returns:
            Active visit log document or None
        """
        return await self.find_one({
            "visitor_id": visitor_id,
            "checked_out_at": None
        })

    async def check_in_visitor(
        self,
        visitor_id: str,
        host_user_id: str,
        purpose: str,
        badge_number: str = None
    ) -> str:
        """
        Create visitor check-in log.

        Args:
            visitor_id: Visitor ID
            host_user_id: Host user ID
            purpose: Visit purpose
            badge_number: Optional badge number

        Returns:
            Created visit log ID
        """
        visit_data = {
            "visitor_id": visitor_id,
            "host_user_id": host_user_id,
            "purpose": purpose,
            "badge_number": badge_number,
            "checked_in_at": datetime.utcnow(),
            "checked_out_at": None
        }
        return await self.insert_one(visit_data)

    async def check_out_visitor(self, visit_log_id: str) -> bool:
        """
        Mark visitor as checked out.

        Args:
            visit_log_id: Visit log ID

        Returns:
            True if checked out successfully
        """
        return await self.update_one(visit_log_id, {
            "checked_out_at": datetime.utcnow()
        })

    async def count_active_visitors(self) -> int:
        """
        Count currently active visitors on campus.

        Returns:
            Number of active visitors
        """
        return await self.count({"checked_out_at": None})


class VisitorPreRegistrationRepository(BaseRepository):
    """Repository for visitor_pre_registrations collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "visitor_pre_registrations")

    async def find_by_access_code(self, access_code: str) -> Optional[Dict[str, Any]]:
        """
        Find pre-registration by access code.

        Args:
            access_code: Access code

        Returns:
            Pre-registration document or None
        """
        return await self.find_one({"access_code": access_code})

    async def find_upcoming_by_host(
        self,
        host_user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find upcoming pre-registrations for a host.

        Args:
            host_user_id: Host user ID
            limit: Maximum number to return

        Returns:
            List of pre-registration documents
        """
        return await self.find_many(
            {
                "host_user_id": host_user_id,
                "expected_date": {"$gte": datetime.utcnow()},
                "status": "pending"
            },
            limit=limit,
            sort=[("expected_date", 1)]
        )

    async def find_by_date(self, date: datetime) -> List[Dict[str, Any]]:
        """
        Find pre-registrations for a specific date.

        Args:
            date: Expected date

        Returns:
            List of pre-registration documents
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return await self.find_many(
            {
                "expected_date": {
                    "$gte": start_of_day,
                    "$lt": end_of_day
                },
                "status": "pending"
            },
            limit=200,
            sort=[("expected_date", 1)]
        )

    async def mark_as_arrived(self, pre_reg_id: str, visit_log_id: str) -> bool:
        """
        Mark pre-registration as arrived.

        Args:
            pre_reg_id: Pre-registration ID
            visit_log_id: Created visit log ID

        Returns:
            True if marked successfully
        """
        return await self.update_one(pre_reg_id, {
            "status": "arrived",
            "visit_log_id": visit_log_id,
            "arrived_at": datetime.utcnow()
        })

    async def mark_as_cancelled(self, pre_reg_id: str, reason: str = None) -> bool:
        """
        Mark pre-registration as cancelled.

        Args:
            pre_reg_id: Pre-registration ID
            reason: Optional cancellation reason

        Returns:
            True if cancelled successfully
        """
        update_data = {
            "status": "cancelled",
            "cancelled_at": datetime.utcnow()
        }
        if reason:
            update_data["cancellation_reason"] = reason

        return await self.update_one(pre_reg_id, update_data)
