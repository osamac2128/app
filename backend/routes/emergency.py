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
    current_user: dict = Depends(require_role(UserRole.ADMIN))
):
    """(Admin only) Trigger a new emergency alert."""
    # db = get_database() - FIXED
    
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
    current_user: dict = Depends(require_role(UserRole.ADMIN))
):
    """(Admin only) Resolve an active alert."""
    # db = get_database() - FIXED
    
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
    current_user: dict = Depends(get_current_active_user)
):
    """Users report their status (Safe/Need Help)."""
    # db = get_database() - FIXED
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
    current_user: dict = Depends(require_role(UserRole.ADMIN))
):
    """(Admin only) Get status of all check-ins for an alert."""
    # db = get_database() - FIXED
    checkins = await db.emergency_checkins.find({'alert_id': alert_id}).to_list(length=1000)
    for c in checkins:
        c['_id'] = str(c['_id'])
    return checkins
