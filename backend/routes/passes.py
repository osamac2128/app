from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime, timedelta
from app.core.database import get_database
from utils.dependencies import get_current_active_user, require_role
from models.passes import (
    Pass, PassCreate, PassUpdate, PassStatus,
    Location, LocationType
)
from models.users import UserRole
from bson import ObjectId

router = APIRouter(prefix='/passes', tags=['Smart Pass'])

@router.get('/locations', response_model=List[Location])
async def get_locations(current_user: dict = Depends(get_current_active_user)):
    """Fetch all active locations."""
    db = get_database()
    locations = await db.locations.find({'is_active': True}).to_list(length=100)
    # Convert _id to string
    for loc in locations:
        loc['_id'] = str(loc['_id'])
    return locations

@router.post('/request', response_model=Pass)
async def request_pass(
    pass_request: PassCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Request a new pass."""
    db = get_database()
    user_id = str(current_user['_id'])
    
    # Check for existing active pass
    active_pass = await db.passes.find_one({
        'student_id': user_id,
        'status': {'$in': [PassStatus.ACTIVE, PassStatus.PENDING, PassStatus.APPROVED]}
    })
    
    if active_pass:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active or pending pass."
        )

    # Create new pass
    new_pass = {
        'student_id': user_id,
        'origin_location_id': pass_request.origin_location_id,
        'destination_location_id': pass_request.destination_location_id,
        'status': PassStatus.ACTIVE, # Auto-approve for now for simplicity
        'requested_at': datetime.utcnow(),
        'departed_at': datetime.utcnow(), # Auto-depart
        'time_limit_minutes': pass_request.time_limit_minutes,
        'is_overtime': False,
        'notes': pass_request.notes,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    result = await db.passes.insert_one(new_pass)
    new_pass['_id'] = str(result.inserted_id)
    
    return new_pass

@router.get('/active', response_model=Pass)
async def get_active_pass(current_user: dict = Depends(get_current_active_user)):
    """Get current user's active pass."""
    db = get_database()
    user_id = str(current_user['_id'])
    
    active_pass = await db.passes.find_one({
        'student_id': user_id,
        'status': PassStatus.ACTIVE
    })
    
    if not active_pass:
        raise HTTPException(status_code=404, detail="No active pass found")
        
    active_pass['_id'] = str(active_pass['_id'])
    return active_pass

@router.post('/end/{pass_id}', response_model=Pass)
async def end_pass(
    pass_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """End an active pass."""
    db = get_database()
    user_id = str(current_user['_id'])
    
    # Verify pass belongs to user
    existing_pass = await db.passes.find_one({
        '_id': ObjectId(pass_id),
        'student_id': user_id,
        'status': PassStatus.ACTIVE
    })
    
    if not existing_pass:
        raise HTTPException(status_code=404, detail="Active pass not found")
        
    update_data = {
        'status': PassStatus.COMPLETED,
        'returned_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    await db.passes.update_one(
        {'_id': ObjectId(pass_id)},
        {'$set': update_data}
    )
    
    existing_pass.update(update_data)
    existing_pass['_id'] = str(existing_pass['_id'])
    
    return existing_pass

@router.get('/hall-monitor', response_model=List[Pass])
async def hall_monitor(
    current_user: dict = Depends(require_role(UserRole.STAFF, UserRole.ADMIN))
):
    """Get all currently active passes (Staff only)."""
    db = get_database()
    
    # Join with users to get student names (simplified for now, just returning passes)
    # In a real app, we'd use an aggregation pipeline to lookup student details
    active_passes = await db.passes.find({'status': PassStatus.ACTIVE}).to_list(length=100)
    
    for p in active_passes:
        p['_id'] = str(p['_id'])
        
    return active_passes
