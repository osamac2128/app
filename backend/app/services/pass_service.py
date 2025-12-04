"""Pass service for hall pass business logic"""

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.pass_repository import PassRepository, LocationRepository
from app.repositories.user_repository import UserRepository
from app.core.exceptions import (
    ValidationException,
    NotFoundException,
    BusinessLogicException
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PassService:
    """Service for hall pass operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize pass service.

        Args:
            db: Motor database instance
        """
        self.db = db
        self.pass_repo = PassRepository(db)
        self.location_repo = LocationRepository(db)
        self.user_repo = UserRepository(db)

    async def request_pass(
        self,
        student_id: str,
        origin_location_id: str,
        destination_location_id: str,
        time_limit_minutes: int = 5,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request a new hall pass.

        Args:
            student_id: Student user ID
            origin_location_id: Origin location ID
            destination_location_id: Destination location ID
            time_limit_minutes: Time limit in minutes
            notes: Optional notes

        Returns:
            Created pass document

        Raises:
            BusinessLogicException: If business rules are violated
            NotFoundException: If location not found
            ValidationException: If validation fails
        """
        # Validate student exists
        student = await self.user_repo.find_by_id(student_id)
        if not student:
            raise NotFoundException("Student not found")

        # Check for existing active or pending pass
        if await self.pass_repo.has_active_or_pending_pass(student_id):
            raise BusinessLogicException(
                "You already have an active or pending pass. "
                "Please end your current pass before requesting a new one."
            )

        # Validate locations exist
        origin = await self.location_repo.find_by_id(origin_location_id)
        destination = await self.location_repo.find_by_id(destination_location_id)

        if not origin:
            raise NotFoundException("Origin location not found")
        if not destination:
            raise NotFoundException("Destination location not found")

        if not destination.get('is_active'):
            raise BusinessLogicException("Destination location is not active")

        # Check location capacity
        if await self.location_repo.is_location_at_capacity(destination_location_id):
            raise BusinessLogicException(
                f"{destination['name']} is currently at capacity. Please try again later."
            )

        # Check daily pass limit (default: 5 passes per day)
        daily_count = await self.pass_repo.count_daily_passes_for_student(student_id)
        max_daily_passes = await self._get_setting('max_daily_passes', 5)
        if daily_count >= max_daily_passes:
            raise BusinessLogicException(
                f"You have reached your daily pass limit of {max_daily_passes} passes."
            )

        # Validate time limit
        if time_limit_minutes < 1 or time_limit_minutes > 60:
            raise ValidationException("Time limit must be between 1 and 60 minutes")

        # Create pass
        now = datetime.utcnow()
        pass_data = {
            'student_id': student_id,
            'origin_location_id': origin_location_id,
            'destination_location_id': destination_location_id,
            'status': 'active',  # Auto-approve for now
            'requested_at': now,
            'departed_at': now,  # Auto-depart
            'time_limit_minutes': time_limit_minutes,
            'is_overtime': False,
            'notes': notes,
        }

        try:
            pass_id = await self.pass_repo.insert_one(pass_data)
            logger.info(f"Pass created: {pass_id} for student {student_id}")

            pass_data['_id'] = pass_id
            return pass_data

        except Exception as e:
            logger.error(f"Error creating pass for student {student_id}: {e}")
            raise

    async def get_active_pass_for_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the active pass for a student.

        Args:
            student_id: Student user ID

        Returns:
            Active pass document or None
        """
        return await self.pass_repo.find_active_pass_by_student(student_id)

    async def end_pass(self, pass_id: str, student_id: str) -> Dict[str, Any]:
        """
        End a hall pass.

        Args:
            pass_id: Pass ID
            student_id: Student user ID (for verification)

        Returns:
            Updated pass document

        Raises:
            NotFoundException: If pass not found
            BusinessLogicException: If pass doesn't belong to student or already ended
        """
        # Get pass
        pass_doc = await self.pass_repo.find_by_id(pass_id)
        if not pass_doc:
            raise NotFoundException("Pass not found")

        # Verify pass belongs to student
        if pass_doc['student_id'] != student_id:
            raise BusinessLogicException("This pass does not belong to you")

        # Check if pass is already ended
        if pass_doc['status'] != 'active':
            raise BusinessLogicException("This pass has already been ended")

        # End pass
        await self.pass_repo.end_pass(pass_id)
        logger.info(f"Pass ended: {pass_id}")

        # Return updated pass
        return await self.pass_repo.find_by_id(pass_id)

    async def get_all_active_passes(self) -> List[Dict[str, Any]]:
        """
        Get all currently active passes (hall monitor view).

        Returns:
            List of active pass documents with student and location info
        """
        passes = await self.pass_repo.find_all_active_passes(limit=200)

        # Enrich with student and location information
        for pass_doc in passes:
            # Get student info
            student = await self.user_repo.find_by_id(pass_doc['student_id'])
            if student:
                pass_doc['student_name'] = f"{student.get('first_name', '')} {student.get('last_name', '')}"
                pass_doc['student_email'] = student.get('email', '')

            # Get location info
            origin = await self.location_repo.find_by_id(pass_doc['origin_location_id'])
            destination = await self.location_repo.find_by_id(pass_doc['destination_location_id'])

            if origin:
                pass_doc['origin_name'] = origin.get('name', 'Unknown')
            if destination:
                pass_doc['destination_name'] = destination.get('name', 'Unknown')

            # Calculate time remaining
            if pass_doc.get('departed_at'):
                elapsed = (datetime.utcnow() - pass_doc['departed_at']).total_seconds() / 60
                time_limit = pass_doc.get('time_limit_minutes', 5)
                pass_doc['time_remaining_minutes'] = max(0, time_limit - elapsed)
                pass_doc['is_overtime'] = elapsed > time_limit

        return passes

    async def get_pass_history_for_student(
        self,
        student_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get pass history for a student.

        Args:
            student_id: Student user ID
            limit: Maximum number of passes to return

        Returns:
            List of pass documents with location info
        """
        passes = await self.pass_repo.find_passes_by_student(student_id, limit)

        # Enrich with location information
        for pass_doc in passes:
            origin = await self.location_repo.find_by_id(pass_doc['origin_location_id'])
            destination = await self.location_repo.find_by_id(pass_doc['destination_location_id'])

            if origin:
                pass_doc['origin_name'] = origin.get('name', 'Unknown')
            if destination:
                pass_doc['destination_name'] = destination.get('name', 'Unknown')

        return passes

    async def approve_pass(self, pass_id: str, approver_id: str) -> Dict[str, Any]:
        """
        Approve a pending pass.

        Args:
            pass_id: Pass ID
            approver_id: Staff user ID

        Returns:
            Updated pass document

        Raises:
            NotFoundException: If pass not found
            BusinessLogicException: If pass is not pending
        """
        pass_doc = await self.pass_repo.find_by_id(pass_id)
        if not pass_doc:
            raise NotFoundException("Pass not found")

        if pass_doc['status'] != 'pending':
            raise BusinessLogicException("Only pending passes can be approved")

        await self.pass_repo.approve_pass(pass_id, approver_id)
        logger.info(f"Pass approved: {pass_id} by {approver_id}")

        return await self.pass_repo.find_by_id(pass_id)

    async def deny_pass(
        self,
        pass_id: str,
        denier_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deny a pending pass.

        Args:
            pass_id: Pass ID
            denier_id: Staff user ID
            reason: Optional denial reason

        Returns:
            Updated pass document

        Raises:
            NotFoundException: If pass not found
            BusinessLogicException: If pass is not pending
        """
        pass_doc = await self.pass_repo.find_by_id(pass_id)
        if not pass_doc:
            raise NotFoundException("Pass not found")

        if pass_doc['status'] != 'pending':
            raise BusinessLogicException("Only pending passes can be denied")

        await self.pass_repo.deny_pass(pass_id, denier_id, reason)
        logger.info(f"Pass denied: {pass_id} by {denier_id}")

        return await self.pass_repo.find_by_id(pass_id)

    async def get_active_locations(self) -> List[Dict[str, Any]]:
        """
        Get all active locations.

        Returns:
            List of active location documents
        """
        return await self.location_repo.find_active_locations()

    async def check_and_mark_overtime_passes(self) -> int:
        """
        Check all active passes and mark overtime ones.
        This should be called periodically (e.g., every minute).

        Returns:
            Number of passes marked as overtime
        """
        active_passes = await self.pass_repo.find_all_active_passes(limit=500)
        overtime_count = 0

        for pass_doc in active_passes:
            if pass_doc.get('departed_at') and not pass_doc.get('is_overtime'):
                elapsed = (datetime.utcnow() - pass_doc['departed_at']).total_seconds() / 60
                time_limit = pass_doc.get('time_limit_minutes', 5)

                if elapsed > time_limit:
                    await self.pass_repo.mark_pass_overtime(pass_doc['_id'])
                    overtime_count += 1
                    logger.warning(f"Pass marked overtime: {pass_doc['_id']}")

        return overtime_count

    async def _get_setting(self, key: str, default: Any) -> Any:
        """
        Get an app setting value.

        Args:
            key: Setting key
            default: Default value if setting not found

        Returns:
            Setting value
        """
        try:
            setting = await self.db.app_settings.find_one({"key": key})
            return setting.get("value", default) if setting else default
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default
