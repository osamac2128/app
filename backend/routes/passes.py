"""Hall pass routes"""

from fastapi import APIRouter, Depends, status
from typing import List
from app.core.database import get_database
from app.services.pass_service import PassService
from app.core.exceptions import (
    ValidationException,
    NotFoundException,
    BusinessLogicException
)
from utils.dependencies import get_current_active_user, require_role
from models.passes import PassCreate, PassRequest, Location
from models.users import UserRole
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix='/passes', tags=['Smart Pass'])


# Dependency to get pass service
async def get_pass_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PassService:
    """Get pass service instance"""
    return PassService(db)


# Routes
@router.get('/locations', response_model=List[Location])
async def get_locations(
    current_user: dict = Depends(get_current_active_user),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Get all active locations.

    Returns a list of all active locations available for hall passes.

    Args:
        current_user: Current authenticated user
        pass_service: Pass service instance

    Returns:
        List of active locations
    """
    return await pass_service.get_active_locations()


@router.post('/request', response_model=dict, status_code=status.HTTP_201_CREATED)
async def request_pass(
    pass_request: PassRequest,
    current_user: dict = Depends(get_current_active_user),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Request a new hall pass.

    Creates a new hall pass for the authenticated student.

    Args:
        pass_request: Pass request details
        current_user: Current authenticated user
        pass_service: Pass service instance

    Returns:
        Created pass document

    Raises:
        BusinessLogicException: If business rules are violated
        NotFoundException: If location not found
        ValidationException: If validation fails
    """
    return await pass_service.request_pass(
        student_id=current_user['_id'],
        origin_location_id=pass_request.origin_location_id,
        destination_location_id=pass_request.destination_location_id,
        time_limit_minutes=pass_request.time_limit_minutes,
        notes=pass_request.notes
    )


@router.get('/active', response_model=dict)
async def get_active_pass(
    current_user: dict = Depends(get_current_active_user),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Get current user's active pass.

    Returns the active hall pass for the authenticated user.

    Args:
        current_user: Current authenticated user
        pass_service: Pass service instance

    Returns:
        Active pass document or None

    Raises:
        NotFoundException: If no active pass found
    """
    pass_doc = await pass_service.get_active_pass_for_student(current_user['_id'])

    if not pass_doc:
        raise NotFoundException("No active pass found")

    return pass_doc


@router.post('/end/{pass_id}', response_model=dict)
async def end_pass(
    pass_id: str,
    current_user: dict = Depends(get_current_active_user),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    End an active pass.

    Marks the specified hall pass as completed.

    Args:
        pass_id: Pass ID to end
        current_user: Current authenticated user
        pass_service: Pass service instance

    Returns:
        Updated pass document

    Raises:
        NotFoundException: If pass not found
        BusinessLogicException: If pass doesn't belong to user or already ended
    """
    return await pass_service.end_pass(pass_id, current_user['_id'])


@router.get('/hall-monitor', response_model=List[dict])
async def hall_monitor(
    current_user: dict = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Get all currently active passes (Staff/Admin only).

    Returns all active hall passes with student and location information
    for hall monitoring purposes.

    Args:
        current_user: Current authenticated user (must be staff or admin)
        pass_service: Pass service instance

    Returns:
        List of active passes with enriched information
    """
    return await pass_service.get_all_active_passes()


@router.get('/history', response_model=List[dict])
async def get_pass_history(
    current_user: dict = Depends(get_current_active_user),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Get pass history for current user.

    Returns the hall pass history for the authenticated user.

    Args:
        current_user: Current authenticated user
        pass_service: Pass service instance

    Returns:
        List of past passes
    """
    return await pass_service.get_pass_history_for_student(
        student_id=current_user['_id'],
        limit=50
    )


@router.post('/approve/{pass_id}', response_model=dict)
async def approve_pass(
    pass_id: str,
    current_user: dict = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Approve a pending pass (Staff/Admin only).

    Approves a pending hall pass request.

    Args:
        pass_id: Pass ID to approve
        current_user: Current authenticated user (must be staff or admin)
        pass_service: Pass service instance

    Returns:
        Updated pass document

    Raises:
        NotFoundException: If pass not found
        BusinessLogicException: If pass is not pending
    """
    return await pass_service.approve_pass(pass_id, current_user['_id'])


@router.post('/deny/{pass_id}', response_model=dict)
async def deny_pass(
    pass_id: str,
    reason: str = None,
    current_user: dict = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Deny a pending pass (Staff/Admin only).

    Denies a pending hall pass request.

    Args:
        pass_id: Pass ID to deny
        reason: Optional denial reason
        current_user: Current authenticated user (must be staff or admin)
        pass_service: Pass service instance

    Returns:
        Updated pass document

    Raises:
        NotFoundException: If pass not found
        BusinessLogicException: If pass is not pending
    """
    return await pass_service.deny_pass(pass_id, current_user['_id'], reason)
