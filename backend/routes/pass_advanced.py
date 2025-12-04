"""Smart Pass Advanced Features - Capacity, No-Fly Times, Encounter Prevention"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime, time as dt_time
from app.core.database import get_database
from utils.dependencies import require_role, get_current_active_user
from models.users import UserRole
from pydantic import BaseModel
from bson import ObjectId

router = APIRouter(prefix='/passes/advanced', tags=['Smart Pass Advanced'])


# ============================================
# MODELS
# ============================================

class NoFlyTimeCreate(BaseModel):
    name: str
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"
    days_of_week: List[int]  # 0=Monday, 6=Sunday
    is_active: bool = True
    description: Optional[str] = None


class NoFlyTimeResponse(BaseModel):
    id: str
    name: str
    start_time: str
    end_time: str
    days_of_week: List[int]
    is_active: bool
    description: Optional[str] = None


class EncounterGroupCreate(BaseModel):
    name: str
    student_ids: List[str]
    reason: str
    is_active: bool = True
    created_by: Optional[str] = None


class EncounterGroupResponse(BaseModel):
    id: str
    name: str
    student_ids: List[str]
    reason: str
    is_active: bool
    created_by: str
    created_at: datetime


class LocationCapacityUpdate(BaseModel):
    max_capacity: int


# ============================================
# NO-FLY TIMES (Passing Periods)
# ============================================

@router.post('/no-fly-times', response_model=NoFlyTimeResponse)
async def create_no_fly_time(
    no_fly_data: NoFlyTimeCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Create a no-fly time restriction.
    
    No-fly times prevent pass requests during specific periods (e.g., passing periods).
    Available to: Admin, Staff
    """
    new_no_fly = no_fly_data.dict()
    new_no_fly['created_by'] = str(current_user['_id'])
    new_no_fly['created_at'] = datetime.utcnow()
    new_no_fly['updated_at'] = datetime.utcnow()
    
    result = await db.no_fly_times.insert_one(new_no_fly)
    new_no_fly['id'] = str(result.inserted_id)
    new_no_fly.pop('_id', None)
    
    return new_no_fly


@router.get('/no-fly-times', response_model=List[NoFlyTimeResponse])
async def get_no_fly_times(
    active_only: bool = True,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get all no-fly time restrictions.
    
    Available to: All authenticated users
    """
    query = {'is_active': True} if active_only else {}
    
    no_fly_times = await db.no_fly_times.find(query).to_list(length=100)
    
    result = []
    for nft in no_fly_times:
        result.append({
            'id': str(nft['_id']),
            'name': nft['name'],
            'start_time': nft['start_time'],
            'end_time': nft['end_time'],
            'days_of_week': nft['days_of_week'],
            'is_active': nft['is_active'],
            'description': nft.get('description')
        })
    
    return result


@router.delete('/no-fly-times/{no_fly_id}')
async def delete_no_fly_time(
    no_fly_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Delete a no-fly time restriction.
    
    Available to: Admin only
    """
    result = await db.no_fly_times.delete_one({'_id': ObjectId(no_fly_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No-fly time not found")
    
    return {"message": "No-fly time deleted successfully"}


@router.get('/check-no-fly')
async def check_no_fly_time(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Check if current time is within a no-fly period.
    
    Returns: {"is_no_fly": bool, "reason": str}
    Available to: All authenticated users
    """
    now = datetime.utcnow()
    current_time = now.strftime("%H:%M")
    current_day = now.weekday()  # 0=Monday, 6=Sunday
    
    # Get active no-fly times
    no_fly_times = await db.no_fly_times.find({'is_active': True}).to_list(length=100)
    
    for nft in no_fly_times:
        # Check if today is in the days_of_week
        if current_day in nft['days_of_week']:
            # Check if current time is within the range
            if nft['start_time'] <= current_time <= nft['end_time']:
                return {
                    "is_no_fly": True,
                    "reason": f"{nft['name']}: {nft.get('description', 'Pass requests not allowed during this time')}"
                }
    
    return {"is_no_fly": False, "reason": None}


# ============================================
# ENCOUNTER PREVENTION (Student Separation)
# ============================================

@router.post('/encounter-groups', response_model=EncounterGroupResponse)
async def create_encounter_group(
    group_data: EncounterGroupCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Create an encounter prevention group.
    
    Students in the same group will not be allowed to have active passes simultaneously.
    Available to: Admin, Staff
    """
    # Validate that all student IDs exist
    for student_id in group_data.student_ids:
        student = await db.users.find_one({'_id': ObjectId(student_id), 'role': 'student'})
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {student_id} not found"
            )
    
    new_group = group_data.dict()
    new_group['created_by'] = str(current_user['_id'])
    new_group['created_at'] = datetime.utcnow()
    new_group['updated_at'] = datetime.utcnow()
    
    result = await db.encounter_groups.insert_one(new_group)
    new_group['id'] = str(result.inserted_id)
    new_group.pop('_id', None)
    
    return new_group


@router.get('/encounter-groups', response_model=List[EncounterGroupResponse])
async def get_encounter_groups(
    active_only: bool = True,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Get all encounter prevention groups.
    
    Available to: Admin, Staff
    """
    query = {'is_active': True} if active_only else {}
    
    groups = await db.encounter_groups.find(query).to_list(length=100)
    
    result = []
    for group in groups:
        result.append({
            'id': str(group['_id']),
            'name': group['name'],
            'student_ids': group['student_ids'],
            'reason': group['reason'],
            'is_active': group['is_active'],
            'created_by': group['created_by'],
            'created_at': group['created_at']
        })
    
    return result


@router.delete('/encounter-groups/{group_id}')
async def delete_encounter_group(
    group_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Delete an encounter prevention group.
    
    Available to: Admin only
    """
    result = await db.encounter_groups.delete_one({'_id': ObjectId(group_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Encounter group not found")
    
    return {"message": "Encounter group deleted successfully"}


@router.get('/check-encounter/{student_id}')
async def check_encounter_prevention(
    student_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Check if a student has encounter prevention conflicts with active passes.
    
    Returns: {"has_conflict": bool, "conflicting_students": List[str], "reason": str}
    Available to: All authenticated users
    """
    # Find all encounter groups containing this student
    groups = await db.encounter_groups.find({
        'is_active': True,
        'student_ids': student_id
    }).to_list(length=100)
    
    if not groups:
        return {"has_conflict": False, "conflicting_students": [], "reason": None}
    
    # Get all student IDs in the same groups
    all_group_student_ids = set()
    group_reasons = []
    
    for group in groups:
        for sid in group['student_ids']:
            if sid != student_id:
                all_group_student_ids.add(sid)
        group_reasons.append(group['reason'])
    
    # Check if any of these students have active passes
    active_passes = await db.passes.find({
        'student_id': {'$in': list(all_group_student_ids)},
        'status': 'active',
        'end_time': None
    }).to_list(length=100)
    
    if active_passes:
        conflicting_students = [p['student_id'] for p in active_passes]
        return {
            "has_conflict": True,
            "conflicting_students": conflicting_students,
            "reason": f"Encounter prevention: {', '.join(group_reasons)}"
        }
    
    return {"has_conflict": False, "conflicting_students": [], "reason": None}


# ============================================
# LOCATION CAPACITY MANAGEMENT
# ============================================

@router.put('/locations/{location_id}/capacity')
async def update_location_capacity(
    location_id: str,
    capacity_data: LocationCapacityUpdate,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Set maximum capacity for a location.
    
    Available to: Admin only
    """
    location = await db.locations.find_one({'_id': ObjectId(location_id)})
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    await db.locations.update_one(
        {'_id': ObjectId(location_id)},
        {'$set': {
            'max_capacity': capacity_data.max_capacity,
            'updated_at': datetime.utcnow()
        }}
    )
    
    return {"message": "Location capacity updated successfully"}


@router.get('/locations/{location_id}/current-capacity')
async def get_current_capacity(
    location_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get current number of students at a location.
    
    Returns: {"location_id": str, "current_count": int, "max_capacity": int, "is_full": bool}
    Available to: All authenticated users
    """
    location = await db.locations.find_one({'_id': ObjectId(location_id)})
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Count active passes to this location
    current_count = await db.passes.count_documents({
        'destination_location_id': location_id,
        'status': 'active',
        'end_time': None
    })
    
    max_capacity = location.get('max_capacity', 999)  # Default high number
    is_full = current_count >= max_capacity
    
    return {
        "location_id": location_id,
        "location_name": location['name'],
        "current_count": current_count,
        "max_capacity": max_capacity,
        "is_full": is_full,
        "available_spots": max(0, max_capacity - current_count)
    }


@router.get('/locations/capacity-status')
async def get_all_location_capacities(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get capacity status for all locations.
    
    Available to: All authenticated users
    """
    locations = await db.locations.find({'is_active': True}).to_list(length=100)
    
    result = []
    for location in locations:
        location_id = str(location['_id'])
        
        # Count active passes to this location
        current_count = await db.passes.count_documents({
            'destination_location_id': location_id,
            'status': 'active',
            'end_time': None
        })
        
        max_capacity = location.get('max_capacity', 999)
        is_full = current_count >= max_capacity
        
        result.append({
            "location_id": location_id,
            "location_name": location['name'],
            "current_count": current_count,
            "max_capacity": max_capacity,
            "is_full": is_full,
            "available_spots": max(0, max_capacity - current_count)
        })
    
    return result
