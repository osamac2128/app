"""Emergency Check-In System - Student accountability during emergencies"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
from app.core.database import get_database
from utils.dependencies import require_role, get_current_active_user
from models.users import UserRole
from pydantic import BaseModel
from bson import ObjectId

router = APIRouter(prefix='/emergency/checkin', tags=['Emergency Check-In'])


# ============================================
# MODELS
# ============================================

class BulkCheckIn(BaseModel):
    student_ids: List[str]
    location: str
    notes: Optional[str] = None


class SingleCheckIn(BaseModel):
    student_id: str
    location: str
    notes: Optional[str] = None


class AssemblyPoint(BaseModel):
    name: str
    location_description: str
    capacity: int
    coordinator_name: str
    is_active: bool = True


# ============================================
# CHECK-IN ENDPOINTS
# ============================================

@router.post('/check-in')
async def check_in_student(
    checkin_data: SingleCheckIn,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Check in a single student during an emergency.
    
    Available to: Admin, Staff
    """
    # Get active emergency
    active_emergency = await db.emergency_alerts.find_one({
        'status': 'active',
        'is_drill': {'$ne': True}
    })
    
    if not active_emergency:
        # Check for active drill
        active_emergency = await db.emergency_alerts.find_one({
            'status': 'active',
            'is_drill': True
        })
    
    if not active_emergency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active emergency or drill"
        )
    
    emergency_id = str(active_emergency['_id'])
    
    # Verify student exists
    student = await db.users.find_one({
        '_id': ObjectId(checkin_data.student_id),
        'role': 'student'
    })
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if already checked in
    existing_checkin = await db.emergency_check_ins.find_one({
        'emergency_id': emergency_id,
        'student_id': checkin_data.student_id
    })
    
    if existing_checkin:
        return {
            "message": "Student already checked in",
            "check_in_time": existing_checkin['check_in_time'],
            "location": existing_checkin['location']
        }
    
    # Create check-in record
    checkin_record = {
        'emergency_id': emergency_id,
        'student_id': checkin_data.student_id,
        'student_name': f"{student['first_name']} {student['last_name']}",
        'location': checkin_data.location,
        'check_in_time': datetime.utcnow(),
        'checked_in_by': str(current_user['_id']),
        'checker_name': f"{current_user['first_name']} {current_user['last_name']}",
        'notes': checkin_data.notes,
        'status': 'safe'
    }
    
    result = await db.emergency_check_ins.insert_one(checkin_record)
    
    return {
        "id": str(result.inserted_id),
        "message": "Student checked in successfully",
        "student_name": checkin_record['student_name'],
        "check_in_time": checkin_record['check_in_time']
    }


@router.post('/bulk-check-in')
async def bulk_check_in_students(
    checkin_data: BulkCheckIn,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Check in multiple students at once (e.g., entire classroom).
    
    Available to: Admin, Staff
    """
    # Get active emergency
    active_emergency = await db.emergency_alerts.find_one({
        'status': {'$in': ['active']}
    })
    
    if not active_emergency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active emergency or drill"
        )
    
    emergency_id = str(active_emergency['_id'])
    
    checked_in_count = 0
    already_checked_in = 0
    errors = []
    
    for student_id in checkin_data.student_ids:
        try:
            # Verify student exists
            student = await db.users.find_one({
                '_id': ObjectId(student_id),
                'role': 'student'
            })
            
            if not student:
                errors.append(f"Student {student_id} not found")
                continue
            
            # Check if already checked in
            existing = await db.emergency_check_ins.find_one({
                'emergency_id': emergency_id,
                'student_id': student_id
            })
            
            if existing:
                already_checked_in += 1
                continue
            
            # Create check-in record
            checkin_record = {
                'emergency_id': emergency_id,
                'student_id': student_id,
                'student_name': f"{student['first_name']} {student['last_name']}",
                'location': checkin_data.location,
                'check_in_time': datetime.utcnow(),
                'checked_in_by': str(current_user['_id']),
                'checker_name': f"{current_user['first_name']} {current_user['last_name']}",
                'notes': checkin_data.notes,
                'status': 'safe'
            }
            
            await db.emergency_check_ins.insert_one(checkin_record)
            checked_in_count += 1
            
        except Exception as e:
            errors.append(f"Error with student {student_id}: {str(e)}")
    
    return {
        "checked_in": checked_in_count,
        "already_checked_in": already_checked_in,
        "errors": errors,
        "total_processed": len(checkin_data.student_ids)
    }


# ============================================
# ACCOUNTABILITY REPORTS
# ============================================

@router.get('/status')
async def get_emergency_accountability_status(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Get current emergency accountability status.
    
    Returns counts of checked-in vs missing students.
    Available to: Admin, Staff
    """
    # Get active emergency
    active_emergency = await db.emergency_alerts.find_one({
        'status': 'active'
    })
    
    if not active_emergency:
        return {
            "active_emergency": False,
            "message": "No active emergency"
        }
    
    emergency_id = str(active_emergency['_id'])
    
    # Get total student count
    total_students = await db.users.count_documents({'role': 'student', 'status': 'active'})
    
    # Get checked-in count
    checked_in_count = await db.emergency_check_ins.count_documents({
        'emergency_id': emergency_id
    })
    
    # Get students in hallways (active passes)
    students_with_active_passes = await db.passes.find({
        'status': 'active',
        'end_time': None
    }).to_list(length=1000)
    
    pass_student_ids = [p['student_id'] for p in students_with_active_passes]
    
    return {
        "active_emergency": True,
        "emergency_id": emergency_id,
        "emergency_type": active_emergency['type'],
        "is_drill": active_emergency.get('is_drill', False),
        "triggered_at": active_emergency['created_at'],
        "total_students": total_students,
        "checked_in": checked_in_count,
        "missing": total_students - checked_in_count,
        "students_with_active_passes": len(pass_student_ids),
        "accountability_percentage": round((checked_in_count / total_students * 100), 2) if total_students > 0 else 0
    }


@router.get('/missing-students')
async def get_missing_students(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Get list of students who haven't checked in during active emergency.
    
    Available to: Admin, Staff
    """
    # Get active emergency
    active_emergency = await db.emergency_alerts.find_one({
        'status': 'active'
    })
    
    if not active_emergency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active emergency"
        )
    
    emergency_id = str(active_emergency['_id'])
    
    # Get all checked-in student IDs
    checked_in_records = await db.emergency_check_ins.find({
        'emergency_id': emergency_id
    }).to_list(length=10000)
    
    checked_in_ids = [r['student_id'] for r in checked_in_records]
    
    # Get all active students NOT in checked-in list
    missing_students = await db.users.find({
        'role': 'student',
        'status': 'active',
        '_id': {'$nin': [ObjectId(sid) for sid in checked_in_ids]}
    }).to_list(length=10000)
    
    result = []
    for student in missing_students:
        student_id = str(student['_id'])
        
        # Check if student has active pass (might be in hallway)
        active_pass = await db.passes.find_one({
            'student_id': student_id,
            'status': 'active',
            'end_time': None
        })
        
        result.append({
            'id': student_id,
            'name': f"{student['first_name']} {student['last_name']}",
            'email': student['email'],
            'has_active_pass': active_pass is not None,
            'last_known_location': active_pass['destination_location_name'] if active_pass else 'Unknown'
        })
    
    return result


# ============================================
# ASSEMBLY POINTS
# ============================================

@router.post('/assembly-points')
async def create_assembly_point(
    point_data: AssemblyPoint,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Create an emergency assembly point.
    
    Available to: Admin only
    """
    new_point = point_data.dict()
    new_point['created_by'] = str(current_user['_id'])
    new_point['created_at'] = datetime.utcnow()
    
    result = await db.assembly_points.insert_one(new_point)
    
    return {
        "id": str(result.inserted_id),
        "message": "Assembly point created successfully"
    }


@router.get('/assembly-points')
async def get_assembly_points(
    active_only: bool = True,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Get all assembly points.
    
    Available to: All authenticated users
    """
    query = {'is_active': True} if active_only else {}
    
    points = await db.assembly_points.find(query).to_list(length=100)
    
    result = []
    for point in points:
        # Get current occupancy
        if active_only:
            active_emergency = await db.emergency_alerts.find_one({'status': 'active'})
            if active_emergency:
                occupancy = await db.emergency_check_ins.count_documents({
                    'emergency_id': str(active_emergency['_id']),
                    'location': point['name']
                })
            else:
                occupancy = 0
        else:
            occupancy = 0
        
        result.append({
            'id': str(point['_id']),
            'name': point['name'],
            'location_description': point['location_description'],
            'capacity': point['capacity'],
            'coordinator_name': point['coordinator_name'],
            'current_occupancy': occupancy,
            'is_full': occupancy >= point['capacity']
        })
    
    return result
