from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
from app.core.database import get_database
from utils.dependencies import get_current_active_user, require_role
from models.emergency import (
    EmergencyAlert, EmergencyAlertCreate, EmergencyAlertUpdate,
    EmergencyCheckIn, EmergencyCheckInCreate, CheckinStatus,
    EmergencyType, SeverityLevel
)
from models.users import UserRole
from bson import ObjectId

router = APIRouter(prefix='/emergency', tags=['Emergency'])

@router.get('/active', response_model=Optional[EmergencyAlert])
async def get_active_alert(current_user: dict = Depends(get_current_active_user), db = Depends(get_database)):
    """Check for any currently active emergency alert."""
    active_alert = await db.emergency_alerts.find_one({
        'resolved_at': None
    })
    
    if active_alert:
        active_alert['_id'] = str(active_alert['_id'])
        return active_alert
    return None

@router.post('/trigger', response_model=EmergencyAlert)
async def trigger_alert(
    alert_data: EmergencyAlertCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """(Admin only) Trigger a new emergency alert."""
    
    # Check if there's already an active alert
    existing_alert = await db.emergency_alerts.find_one({'resolved_at': None})
    if existing_alert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already an active emergency alert."
        )
    
    new_alert = alert_data.dict()
    new_alert['triggered_at'] = datetime.utcnow()
    new_alert['created_at'] = datetime.utcnow()
    # triggered_by is passed in body, but we should override/verify with current user
    new_alert['triggered_by'] = str(current_user['_id'])
    
    result = await db.emergency_alerts.insert_one(new_alert)
    new_alert['_id'] = str(result.inserted_id)
    
    return new_alert

@router.post('/resolve/{alert_id}', response_model=EmergencyAlert)
async def resolve_alert(
    alert_id: str,
    resolution_notes: Optional[str] = None,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """(Admin only) Resolve an active alert."""
    
    alert = await db.emergency_alerts.find_one({'_id': ObjectId(alert_id)})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    if alert['resolved_at']:
        raise HTTPException(status_code=400, detail="Alert is already resolved")
        
    update_data = {
        'resolved_at': datetime.utcnow(),
        'resolved_by': str(current_user['_id']),
        'resolution_notes': resolution_notes
    }
    
    await db.emergency_alerts.update_one(
        {'_id': ObjectId(alert_id)},
        {'$set': update_data}
    )
    
    alert.update(update_data)
    alert['_id'] = str(alert['_id'])
    return alert

@router.post('/check-in', response_model=EmergencyCheckIn)
async def check_in(
    checkin_data: EmergencyCheckInCreate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Users report their status (Safe/Need Help)."""
    user_id = str(current_user['_id'])
    
    # Verify alert exists and is active
    alert = await db.emergency_alerts.find_one({'_id': ObjectId(checkin_data.alert_id)})
    if not alert or alert['resolved_at']:
        raise HTTPException(status_code=400, detail="Invalid or inactive alert")
        
    # Check if user already checked in
    existing_checkin = await db.emergency_checkins.find_one({
        'alert_id': checkin_data.alert_id,
        'user_id': user_id
    })
    
    if existing_checkin:
        # Update existing check-in
        update_data = {
            'status': checkin_data.status,
            'location': checkin_data.location,
            'updated_at': datetime.utcnow()
        }
        await db.emergency_checkins.update_one(
            {'_id': existing_checkin['_id']},
            {'$set': update_data}
        )
        existing_checkin.update(update_data)
        existing_checkin['_id'] = str(existing_checkin['_id'])
        return existing_checkin
    else:
        # Create new check-in
        new_checkin = checkin_data.dict()
        new_checkin['user_id'] = user_id
        new_checkin['checked_in_at'] = datetime.utcnow()
        new_checkin['created_at'] = datetime.utcnow()
        new_checkin['updated_at'] = datetime.utcnow()
        
        result = await db.emergency_checkins.insert_one(new_checkin)
        new_checkin['_id'] = str(result.inserted_id)
        return new_checkin

@router.get('/status/{alert_id}', response_model=List[EmergencyCheckIn])
async def get_alert_status(
    alert_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Get status of all check-ins for an alert."""
    checkins = await db.emergency_checkins.find({'alert_id': alert_id}).to_list(length=1000)
    for c in checkins:
        c['_id'] = str(c['_id'])
    return checkins


@router.get('/history', response_model=List[EmergencyAlert])
async def get_emergency_history(
    limit: int = 50,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Get emergency alert history."""
    alerts = await db.emergency_alerts.find().sort('triggered_at', -1).limit(limit).to_list(length=limit)
    for alert in alerts:
        alert['_id'] = str(alert['_id'])
    return alerts


@router.post('/drill/schedule')
async def schedule_drill(
    drill_data: dict,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """(Admin only) Schedule an emergency drill."""
    drill_data['scheduled_by'] = str(current_user['_id'])
    drill_data['is_drill'] = True
    drill_data['created_at'] = datetime.utcnow()
    
    result = await db.emergency_drills.insert_one(drill_data)
    drill_data['_id'] = str(result.inserted_id)
    
    return drill_data


@router.get('/drill/upcoming')
async def get_upcoming_drills(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Get upcoming scheduled drills."""
    drills = await db.emergency_drills.find({
        'scheduled_date': {'$gte': datetime.utcnow()},
        'completed': {'$ne': True}
    }).to_list(length=100)
    
    for drill in drills:
        drill['_id'] = str(drill['_id'])
    
    return drills


@router.post('/reunification/check-in')
async def reunification_check_in(
    data: dict,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Parent check-in at reunification point."""
    reunion_data = {
        'alert_id': data.get('alert_id'),
        'parent_id': data.get('parent_id'),
        'parent_name': data.get('parent_name'),
        'check_in_time': datetime.utcnow(),
        'station': data.get('station', 'main'),
        'checked_in_by': str(current_user['_id']),
        'status': 'checked_in'
    }
    
    result = await db.reunifications.insert_one(reunion_data)
    reunion_data['_id'] = str(result.inserted_id)
    
    return reunion_data


@router.post('/reunification/release-student')
async def release_student(
    data: dict,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Release student to authorized person."""
    release_data = {
        'alert_id': data.get('alert_id'),
        'student_id': data.get('student_id'),
        'released_to': data.get('released_to'),
        'released_to_name': data.get('released_to_name'),
        'release_time': datetime.utcnow(),
        'released_by': str(current_user['_id']),
        'signature': data.get('signature'),
        'notes': data.get('notes')
    }
    
    result = await db.student_releases.insert_one(release_data)
    release_data['_id'] = str(result.inserted_id)
    
    # Update student status
    await db.emergency_checkins.update_one(
        {'alert_id': data.get('alert_id'), 'user_id': data.get('student_id')},
        {'$set': {'released': True, 'released_at': datetime.utcnow()}}
    )
    
    return release_data


@router.get('/reunification/status/{alert_id}')
async def get_reunification_status(
    alert_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Get reunification status for an alert."""
    total_students = await db.users.count_documents({'role': 'student', 'status': 'active'})
    checked_in_parents = await db.reunifications.count_documents({'alert_id': alert_id})
    released_students = await db.student_releases.count_documents({'alert_id': alert_id})
    
    # Get list of released students
    releases = await db.student_releases.find({'alert_id': alert_id}).to_list(length=1000)
    for r in releases:
        r['_id'] = str(r['_id'])
        # Enrich with student info
        student = await db.users.find_one({'_id': ObjectId(r['student_id'])})
        if student:
            r['student_name'] = f"{student.get('first_name')} {student.get('last_name')}"
    
    return {
        'alert_id': alert_id,
        'total_students': total_students,
        'checked_in_parents': checked_in_parents,
        'released_students': released_students,
        'remaining_students': total_students - released_students,
        'releases': releases
    }
