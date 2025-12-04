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


@router.get('/teacher/pending', response_model=List[dict])
async def get_teacher_pending_passes(
    current_user: dict = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    pass_service: PassService = Depends(get_pass_service),
    db = Depends(get_database)
):
    """
    Get pending passes requiring teacher approval.
    
    Returns all passes that need approval from the current teacher.
    """
    from bson import ObjectId
    
    # Get pending passes
    pending_passes = await db.passes.find({
        'status': 'pending',
        'requires_approval': True
    }).sort('created_at', -1).to_list(length=100)
    
    # Enrich with student info
    for pass_doc in pending_passes:
        pass_doc['_id'] = str(pass_doc['_id'])
        
        # Get student info
        student = await db.users.find_one({'_id': ObjectId(pass_doc['student_id'])})
        if student:
            pass_doc['student'] = {
                'name': f"{student.get('first_name')} {student.get('last_name')}",
                'email': student.get('email')
            }
        
        # Get location names
        if pass_doc.get('origin_location_id'):
            origin = await db.locations.find_one({'_id': ObjectId(pass_doc['origin_location_id'])})
            if origin:
                pass_doc['origin_name'] = origin.get('name')
                
        if pass_doc.get('destination_location_id'):
            dest = await db.locations.find_one({'_id': ObjectId(pass_doc['destination_location_id'])})
            if dest:
                pass_doc['destination_name'] = dest.get('name')
    
    return pending_passes


@router.post('/bulk-approve')
async def bulk_approve_passes(
    pass_ids: List[str],
    current_user: dict = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Bulk approve multiple passes.
    
    Allows teachers to approve multiple passes at once.
    """
    results = []
    for pass_id in pass_ids:
        try:
            result = await pass_service.approve_pass(pass_id, current_user['_id'])
            results.append({'pass_id': pass_id, 'status': 'approved', 'data': result})
        except Exception as e:
            results.append({'pass_id': pass_id, 'status': 'error', 'error': str(e)})
    
    return {'results': results}


@router.get('/overtime', response_model=List[dict])
async def get_overtime_passes(
    current_user: dict = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Get all overtime passes.
    
    Returns passes that have exceeded their time limit.
    """
    from datetime import datetime, timedelta
    from bson import ObjectId
    from app.core.database import get_database
    
    db = await anext(get_database())
    
    # Get active passes that are overtime
    now = datetime.utcnow()
    overtime_passes = await db.passes.find({
        'status': 'active',
        'expected_return_time': {'$lt': now}
    }).to_list(length=100)
    
    # Enrich with info
    for pass_doc in overtime_passes:
        pass_doc['_id'] = str(pass_doc['_id'])
        pass_doc['minutes_overtime'] = int((now - pass_doc['expected_return_time']).total_seconds() / 60)
        
        # Get student info
        student = await db.users.find_one({'_id': ObjectId(pass_doc['student_id'])})
        if student:
            pass_doc['student'] = {
                'name': f"{student.get('first_name')} {student.get('last_name')}",
                'email': student.get('email')
            }
        
        # Get location name
        if pass_doc.get('destination_location_id'):
            dest = await db.locations.find_one({'_id': ObjectId(pass_doc['destination_location_id'])})
            if dest:
                pass_doc['destination_name'] = dest.get('name')
    
    return overtime_passes


@router.post('/extend/{pass_id}')
async def extend_pass(
    pass_id: str,
    additional_minutes: int,
    current_user: dict = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    pass_service: PassService = Depends(get_pass_service)
):
    """
    Extend an active pass.
    
    Adds additional time to an active pass.
    """
    from datetime import datetime, timedelta
    from bson import ObjectId
    from app.core.database import get_database
    
    db = await anext(get_database())
    
    pass_doc = await db.passes.find_one({'_id': ObjectId(pass_id)})
    if not pass_doc:
        raise NotFoundException("Pass not found")
    
    if pass_doc.get('status') != 'active':
        raise BusinessLogicException("Can only extend active passes")
    
    # Update expected return time
    new_return_time = pass_doc['expected_return_time'] + timedelta(minutes=additional_minutes)
    
    await db.passes.update_one(
        {'_id': ObjectId(pass_id)},
        {'$set': {
            'expected_return_time': new_return_time,
            'extended_by': str(current_user['_id']),
            'extension_minutes': additional_minutes,
            'extended_at': datetime.utcnow()
        }}
    )
    
    return {
        'message': f'Pass extended by {additional_minutes} minutes',
        'new_return_time': new_return_time.isoformat()
    }
