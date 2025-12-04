"""Digital ID repository for digital ID database operations"""

from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base_repository import BaseRepository
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DigitalIDRepository(BaseRepository):
    """Repository for digital_ids collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "digital_ids")

    async def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Find digital ID by user ID.

        Args:
            user_id: User ID

        Returns:
            Digital ID document or None
        """
        return await self.find_one({"user_id": user_id})

    async def find_by_qr_code(self, qr_code: str) -> Optional[Dict[str, Any]]:
        """
        Find digital ID by QR code.

        Args:
            qr_code: QR code string

        Returns:
            Digital ID document or None
        """
        return await self.find_one({"qr_code": qr_code})

    async def find_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """
        Find digital ID by barcode.

        Args:
            barcode: Barcode string

        Returns:
            Digital ID document or None
        """
        return await self.find_one({"barcode": barcode})

    async def find_active_ids(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Find all active digital IDs.

        Args:
            limit: Maximum number of IDs to return

        Returns:
            List of active digital ID documents
        """
        return await self.find_many({"is_active": True}, limit=limit)

    async def find_pending_photo_approvals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Find digital IDs with pending photo approvals.

        Args:
            limit: Maximum number of IDs to return

        Returns:
            List of digital IDs pending photo approval
        """
        return await self.find_many({"photo_status": "pending"}, limit=limit)

    async def activate_id(self, id: str) -> bool:
        """
        Activate a digital ID.

        Args:
            id: Digital ID document ID

        Returns:
            True if activated successfully
        """
        return await self.update_one(id, {"is_active": True})

    async def deactivate_id(self, id: str) -> bool:
        """
        Deactivate a digital ID.

        Args:
            id: Digital ID document ID

        Returns:
            True if deactivated successfully
        """
        return await self.update_one(id, {"is_active": False})

    async def approve_photo(self, id: str, approved_by: str) -> bool:
        """
        Approve a pending photo.

        Args:
            id: Digital ID document ID
            approved_by: User ID of approver

        Returns:
            True if approved successfully
        """
        return await self.update_one(id, {
            "photo_status": "approved",
            "photo_approved_by": approved_by,
            "photo_approved_at": datetime.utcnow()
        })

    async def reject_photo(self, id: str, rejected_by: str, reason: str = None) -> bool:
        """
        Reject a pending photo.

        Args:
            id: Digital ID document ID
            rejected_by: User ID of rejecter
            reason: Optional rejection reason

        Returns:
            True if rejected successfully
        """
        update_data = {
            "photo_status": "rejected",
            "photo_rejected_by": rejected_by,
            "photo_rejected_at": datetime.utcnow()
        }
        if reason:
            update_data["photo_rejection_reason"] = reason

        return await self.update_one(id, update_data)


class IDScanLogRepository(BaseRepository):
    """Repository for id_scan_logs collection operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, "id_scan_logs")

    async def find_scans_by_digital_id(
        self,
        digital_id_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find scan logs for a digital ID.

        Args:
            digital_id_id: Digital ID document ID
            limit: Maximum number of scans to return

        Returns:
            List of scan log documents
        """
        return await self.find_many(
            {"digital_id_id": digital_id_id},
            limit=limit,
            sort=[("scanned_at", -1)]
        )

    async def find_scans_by_scanner(
        self,
        scanned_by: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find scan logs by scanner user ID.

        Args:
            scanned_by: Scanner user ID
            limit: Maximum number of scans to return

        Returns:
            List of scan log documents
        """
        return await self.find_many(
            {"scanned_by": scanned_by},
            limit=limit,
            sort=[("scanned_at", -1)]
        )

    async def log_scan(
        self,
        digital_id_id: str,
        scanned_by: str,
        scan_type: str,
        location: str = None
    ) -> str:
        """
        Log a digital ID scan.

        Args:
            digital_id_id: Digital ID document ID
            scanned_by: Scanner user ID
            scan_type: Type of scan (qr, barcode)
            location: Optional scan location

        Returns:
            Created scan log ID
        """
        scan_data = {
            "digital_id_id": digital_id_id,
            "scanned_by": scanned_by,
            "scan_type": scan_type,
            "location": location,
            "scanned_at": datetime.utcnow()
        }
        return await self.insert_one(scan_data)
