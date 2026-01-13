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

# Predefined emergency alert templates
EMERGENCY_TEMPLATES = {
    "lockdown": {
        "type": "lockdown",
        "title": "LOCKDOWN - Immediate Threat",
        "message": "This is a LOCKDOWN. An immediate threat has been identified. Lock all doors. Turn off lights. Move away from windows and doors. Stay silent. Do not open doors for anyone. Wait for the all-clear signal.",
        "instructions": "1. Lock doors immediately\n2. Turn off lights\n3. Move away from windows\n4. Stay quiet and out of sight\n5. Silence all phones\n6. Wait for all-clear",
        "severity": "critical",
        "color": "#DC2626",
        "icon": "lock-closed"
    },
    "lockdown_secure": {
        "type": "lockdown_secure",
        "title": "SECURE - Potential Threat",
        "message": "This is a SECURE alert. A potential threat has been identified. Lock all doors and continue normal activities quietly. Do not allow entry to anyone until further notice.",
        "instructions": "1. Lock classroom doors\n2. Continue activities quietly\n3. Do not allow entry\n4. Monitor communications\n5. Wait for updates",
        "severity": "high",
        "color": "#F59E0B",
        "icon": "shield-checkmark"
    },
    "fire": {
        "type": "fire",
        "title": "FIRE EVACUATION",
        "message": "A fire has been detected. Evacuate immediately using the nearest safe exit. Do not use elevators. Proceed to designated assembly areas. Account for all personnel.",
        "instructions": "1. Evacuate immediately\n2. Use nearest safe exit\n3. Do NOT use elevators\n4. Close doors behind you\n5. Go to assembly area\n6. Wait for roll call",
        "severity": "critical",
        "color": "#EF4444",
        "icon": "flame"
    },
    "fire_drill": {
        "type": "fire_drill",
        "title": "FIRE DRILL - Practice",
        "message": "This is a FIRE DRILL. Please evacuate the building using your designated route. Proceed to your assembly area for roll call. This is only a drill.",
        "instructions": "1. Exit the building calmly\n2. Use designated routes\n3. Do NOT use elevators\n4. Go to assembly area\n5. Wait for roll call\n6. This is a drill",
        "severity": "low",
        "color": "#F59E0B",
        "icon": "flame"
    },
    "tornado": {
        "type": "tornado",
        "title": "TORNADO WARNING",
        "message": "A tornado warning is in effect for this area. Move immediately to designated shelter areas. Stay away from windows and exterior walls. Protect your head and neck.",
        "instructions": "1. Move to shelter area NOW\n2. Stay away from windows\n3. Move to lowest floor\n4. Get under sturdy furniture\n5. Protect head and neck\n6. Wait for all-clear",
        "severity": "critical",
        "color": "#8B5CF6",
        "icon": "thunderstorm"
    },
    "tornado_drill": {
        "type": "tornado_drill",
        "title": "TORNADO DRILL - Practice",
        "message": "This is a TORNADO DRILL. Please proceed to designated shelter areas. Practice duck and cover positions. This is only a drill.",
        "instructions": "1. Move to shelter area\n2. Practice duck and cover\n3. Stay away from windows\n4. Remain in position\n5. This is a drill",
        "severity": "low",
        "color": "#8B5CF6",
        "icon": "thunderstorm"
    },
    "earthquake": {
        "type": "earthquake",
        "title": "EARTHQUAKE - Drop, Cover, Hold",
        "message": "An earthquake is occurring or has just occurred. DROP, COVER, and HOLD ON. Get under a desk or sturdy table. Stay away from windows. After shaking stops, evacuate if safe.",
        "instructions": "1. DROP to the ground\n2. Take COVER under desk\n3. HOLD ON until shaking stops\n4. Stay away from windows\n5. Evacuate when safe\n6. Watch for aftershocks",
        "severity": "critical",
        "color": "#9333EA",
        "icon": "pulse"
    },
    "earthquake_drill": {
        "type": "earthquake_drill",
        "title": "EARTHQUAKE DRILL - Practice",
        "message": "This is an EARTHQUAKE DRILL. Practice Drop, Cover, and Hold On. This is only a drill.",
        "instructions": "1. DROP to the ground\n2. Take COVER under desk\n3. HOLD ON for 60 seconds\n4. This is a drill",
        "severity": "low",
        "color": "#9333EA",
        "icon": "pulse"
    },
    "medical": {
        "type": "medical",
        "title": "MEDICAL EMERGENCY",
        "message": "A medical emergency has been reported. Medical personnel have been dispatched. Please clear the area and allow emergency responders access. Report any additional medical needs.",
        "instructions": "1. Clear the affected area\n2. Allow responder access\n3. Do not crowd the area\n4. Report other emergencies\n5. Follow staff directions",
        "severity": "high",
        "color": "#EF4444",
        "icon": "medical"
    },
    "shelter_in_place": {
        "type": "shelter_in_place",
        "title": "SHELTER IN PLACE",
        "message": "Due to an external threat or environmental hazard, please shelter in place. Close all windows and doors. Turn off HVAC if possible. Remain inside until further notice.",
        "instructions": "1. Go inside immediately\n2. Close all windows/doors\n3. Turn off HVAC if possible\n4. Seal gaps if needed\n5. Stay away from windows\n6. Wait for all-clear",
        "severity": "high",
        "color": "#3B82F6",
        "icon": "home"
    },
    "evacuation": {
        "type": "evacuation",
        "title": "EVACUATION REQUIRED",
        "message": "Building evacuation is required. Leave the building immediately using the nearest safe exit. Proceed to designated assembly areas. Do not re-enter until authorized.",
        "instructions": "1. Leave building immediately\n2. Use nearest safe exit\n3. Do NOT use elevators\n4. Go to assembly area\n5. Wait for roll call\n6. Do NOT re-enter",
        "severity": "high",
        "color": "#DC2626",
        "icon": "exit"
    },
    "all_clear": {
        "type": "all_clear",
        "title": "ALL CLEAR",
        "message": "The emergency has been resolved. It is now safe to resume normal activities. Thank you for your cooperation during this situation.",
        "instructions": "1. Emergency is resolved\n2. Resume normal activities\n3. Report any concerns\n4. Thank you for cooperating",
        "severity": "info",
        "color": "#10B981",
        "icon": "checkmark-circle"
    },
    "police_activity": {
        "type": "police_activity",
        "title": "POLICE ACTIVITY NEARBY",
        "message": "There is police activity in the vicinity. As a precaution, please remain inside and away from windows. Continue normal activities quietly. Updates will follow.",
        "instructions": "1. Remain inside\n2. Stay away from windows\n3. Continue quietly\n4. Monitor updates\n5. Do not leave campus",
        "severity": "medium",
        "color": "#3B82F6",
        "icon": "shield"
    },
    "hazmat": {
        "type": "hazmat",
        "title": "HAZMAT - Chemical Hazard",
        "message": "A chemical or hazardous material incident has been reported. Shelter in place immediately. Close all windows and doors. Turn off HVAC systems. Cover nose and mouth if needed.",
        "instructions": "1. Shelter in place NOW\n2. Close all windows/doors\n3. Turn off HVAC\n4. Cover nose and mouth\n5. Move to interior room\n6. Wait for all-clear",
        "severity": "critical",
        "color": "#F59E0B",
        "icon": "warning"
    }
}

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


@router.get('/templates')
async def get_emergency_templates(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
):
    """(Admin/Staff) Get all emergency alert templates."""
    return list(EMERGENCY_TEMPLATES.values())


@router.get('/templates/{template_type}')
async def get_emergency_template(
    template_type: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
):
    """(Admin/Staff) Get a specific emergency alert template."""
    if template_type not in EMERGENCY_TEMPLATES:
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_type}' not found. Available: {list(EMERGENCY_TEMPLATES.keys())}"
        )
    return EMERGENCY_TEMPLATES[template_type]


@router.get('/active-passes')
async def get_active_passes_during_emergency(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    (Admin/Staff) Get all active hall passes during an emergency.
    Shows all students currently in hallways/outside classrooms.
    """
    # Check if there's an active emergency
    active_alert = await db.emergency_alerts.find_one({'resolved_at': None})

    # Get all active passes (regardless of emergency status - useful for safety)
    active_passes = await db.passes.find({
        'status': {'$in': ['active', 'approved']}
    }).to_list(length=500)

    result = []
    for pass_doc in active_passes:
        # Get student info
        student = await db.users.find_one({'_id': ObjectId(pass_doc['student_id'])})

        # Get origin location
        origin = await db.locations.find_one({'_id': ObjectId(pass_doc['origin_location_id'])})

        # Get destination location
        destination = await db.locations.find_one({'_id': ObjectId(pass_doc['destination_location_id'])})

        # Calculate time out
        departed_at = pass_doc.get('departed_at') or pass_doc.get('approved_at')
        time_out_minutes = 0
        if departed_at:
            time_out_minutes = int((datetime.utcnow() - departed_at).total_seconds() / 60)

        result.append({
            '_id': str(pass_doc['_id']),
            'student': {
                '_id': str(student['_id']) if student else None,
                'name': f"{student.get('first_name', '')} {student.get('last_name', '')}" if student else 'Unknown',
                'email': student.get('email') if student else None,
                'role': student.get('role') if student else None
            } if student else None,
            'origin': {
                '_id': str(origin['_id']) if origin else None,
                'name': origin.get('name', 'Unknown') if origin else 'Unknown'
            } if origin else None,
            'destination': {
                '_id': str(destination['_id']) if destination else None,
                'name': destination.get('name', 'Unknown') if destination else 'Unknown'
            } if destination else None,
            'status': pass_doc.get('status'),
            'departed_at': pass_doc.get('departed_at'),
            'time_out_minutes': time_out_minutes,
            'time_limit_minutes': pass_doc.get('time_limit_minutes', 10),
            'is_overtime': time_out_minutes > pass_doc.get('time_limit_minutes', 10),
            'notes': pass_doc.get('notes')
        })

    return {
        'emergency_active': active_alert is not None,
        'emergency_type': active_alert.get('type') if active_alert else None,
        'total_students_out': len(result),
        'passes': result
    }


@router.get('/accountability-report')
async def get_accountability_report(
    alert_id: Optional[str] = None,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    (Admin/Staff) Get comprehensive accountability report during emergency.
    Includes check-ins and students with active hall passes.
    """
    # Get active alert if no alert_id specified
    if not alert_id:
        active_alert = await db.emergency_alerts.find_one({'resolved_at': None})
        if not active_alert:
            raise HTTPException(
                status_code=400,
                detail="No active emergency. Specify alert_id for historical data."
            )
        alert_id = str(active_alert['_id'])

    # Get all students
    all_students = await db.users.find({
        'role': 'student',
        'status': 'active'
    }).to_list(length=2000)

    # Get check-ins for this alert
    checkins = await db.emergency_checkins.find({
        'alert_id': alert_id
    }).to_list(length=2000)
    checkin_map = {c['user_id']: c for c in checkins}

    # Get active passes
    active_passes = await db.passes.find({
        'status': {'$in': ['active', 'approved']}
    }).to_list(length=500)
    active_pass_map = {p['student_id']: p for p in active_passes}

    # Build accountability list
    checked_in_safe = []
    checked_in_need_help = []
    in_hallway = []
    not_checked_in = []

    for student in all_students:
        student_id = str(student['_id'])
        student_info = {
            '_id': student_id,
            'name': f"{student.get('first_name', '')} {student.get('last_name', '')}",
            'email': student.get('email')
        }

        # Check if student has active pass (in hallway)
        if student_id in active_pass_map:
            pass_doc = active_pass_map[student_id]
            destination = await db.locations.find_one({'_id': ObjectId(pass_doc['destination_location_id'])})
            student_info['location'] = destination.get('name', 'Unknown') if destination else 'Unknown'
            student_info['pass_id'] = str(pass_doc['_id'])
            in_hallway.append(student_info)
        # Check if student checked in
        elif student_id in checkin_map:
            checkin = checkin_map[student_id]
            student_info['status'] = checkin.get('status')
            student_info['location'] = checkin.get('location')
            student_info['checked_in_at'] = checkin.get('checked_in_at')

            if checkin.get('status') in ['safe', 'safe_with_injuries']:
                checked_in_safe.append(student_info)
            else:
                checked_in_need_help.append(student_info)
        else:
            not_checked_in.append(student_info)

    return {
        'alert_id': alert_id,
        'summary': {
            'total_students': len(all_students),
            'checked_in_safe': len(checked_in_safe),
            'need_help': len(checked_in_need_help),
            'in_hallway': len(in_hallway),
            'not_checked_in': len(not_checked_in),
            'accounted_for': len(checked_in_safe) + len(checked_in_need_help) + len(in_hallway)
        },
        'students_safe': checked_in_safe,
        'students_need_help': checked_in_need_help,
        'students_in_hallway': in_hallway,
        'students_not_checked_in': not_checked_in
    }
