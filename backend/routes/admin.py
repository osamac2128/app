"""Admin-only routes for system management"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.database import get_database
from utils.dependencies import get_current_active_user, require_role
from models.users import UserRole
from models.passes import Location, LocationCreate
from bson import ObjectId
import csv
import io
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix='/admin', tags=['Admin'])


# ============================================
# ROLE HIERARCHY CHECKS
# ============================================

SUPER_ADMIN_EMAILS = ['osama.chaudhry@gmail.com', 'ochaudhry@aisj.edu.sa']

def is_super_admin(user: dict) -> bool:
    """Check if user is a super admin"""
    return user.get('email', '').lower() in SUPER_ADMIN_EMAILS

def is_admin_or_higher(user: dict) -> bool:
    """Check if user is admin or super admin"""
    return user.get('role') == UserRole.ADMIN

async def require_super_admin(current_user: dict = Depends(require_role(UserRole.ADMIN))):
    """Dependency to require super admin access"""
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires super admin privileges"
        )
    return current_user


# ============================================
# PHASE 1: DASHBOARD & ANALYTICS
# ============================================

class DashboardStats(BaseModel):
    """Dashboard statistics model"""
    total_users: Dict[str, int]
    active_passes_count: int
    pending_id_approvals: int
    recent_emergency_count: int
    today_activity: Dict[str, Any]

@router.get('/dashboard/stats', response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Get overall dashboard statistics.
    
    Available to: Admin, Staff (limited view)
    """
    # Total users by role
    total_users = {}
    for role in ['student', 'parent', 'staff', 'admin']:
        count = await db.users.count_documents({'role': role, 'status': 'active'})
        total_users[role] = count
    
    # Active passes
    active_passes_count = await db.passes.count_documents({
        'status': 'active',
        'end_time': None
    })
    
    # Pending ID approvals
    pending_id_approvals = await db.digital_ids.count_documents({
        'photo_status': 'pending'
    })
    
    # Recent emergency alerts (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_emergency_count = await db.emergency_alerts.count_documents({
        'triggered_at': {'$gte': thirty_days_ago}
    })
    
    # Today's activity
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_passes = await db.passes.count_documents({
        'created_at': {'$gte': today_start}
    })
    today_logins = await db.users.count_documents({
        'last_login_at': {'$gte': today_start}
    })
    
    return {
        'total_users': total_users,
        'active_passes_count': active_passes_count,
        'pending_id_approvals': pending_id_approvals,
        'recent_emergency_count': recent_emergency_count,
        'today_activity': {
            'passes_created': today_passes,
            'user_logins': today_logins
        }
    }


class PassAnalytics(BaseModel):
    """Pass analytics model"""
    most_used_locations: List[Dict[str, Any]]
    average_duration_minutes: float
    overtime_count: int
    total_passes_today: int
    total_passes_week: int
    hourly_distribution: List[Dict[str, Any]]

@router.get('/analytics/passes', response_model=PassAnalytics)
async def get_pass_analytics(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Get Smart Pass analytics.
    
    Available to: Admin, Staff
    """
    # Most used locations (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Aggregate most used locations
    most_used_pipeline = [
        {'$match': {'created_at': {'$gte': seven_days_ago}}},
        {'$group': {
            '_id': '$destination_location_id',
            'count': {'$sum': 1}
        }},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    
    most_used_cursor = db.passes.aggregate(most_used_pipeline)
    most_used_raw = await most_used_cursor.to_list(length=5)
    
    # Enrich with location names
    most_used_locations = []
    for item in most_used_raw:
        location = await db.locations.find_one({'_id': ObjectId(item['_id'])})
        most_used_locations.append({
            'location_name': location.get('name', 'Unknown') if location else 'Unknown',
            'count': item['count']
        })
    
    # Average duration
    completed_passes = await db.passes.find({
        'status': 'completed',
        'created_at': {'$gte': seven_days_ago}
    }).to_list(length=1000)
    
    total_duration = 0
    count = 0
    for pass_doc in completed_passes:
        if pass_doc.get('start_time') and pass_doc.get('end_time'):
            duration = (pass_doc['end_time'] - pass_doc['start_time']).total_seconds() / 60
            total_duration += duration
            count += 1
    
    average_duration = total_duration / count if count > 0 else 0
    
    # Overtime count (last 7 days)
    overtime_count = await db.passes.count_documents({
        'is_overtime': True,
        'created_at': {'$gte': seven_days_ago}
    })
    
    # Today's passes
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_passes_today = await db.passes.count_documents({
        'created_at': {'$gte': today_start}
    })
    
    # Week's passes
    total_passes_week = await db.passes.count_documents({
        'created_at': {'$gte': seven_days_ago}
    })
    
    # Hourly distribution (today)
    hourly_distribution = []
    for hour in range(24):
        hour_start = today_start.replace(hour=hour)
        hour_end = hour_start + timedelta(hours=1)
        count = await db.passes.count_documents({
            'created_at': {'$gte': hour_start, '$lt': hour_end}
        })
        if count > 0:  # Only include hours with activity
            hourly_distribution.append({
                'hour': hour,
                'count': count
            })
    
    return {
        'most_used_locations': most_used_locations,
        'average_duration_minutes': round(average_duration, 2),
        'overtime_count': overtime_count,
        'total_passes_today': total_passes_today,
        'total_passes_week': total_passes_week,
        'hourly_distribution': hourly_distribution
    }


class IDAnalytics(BaseModel):
    """ID card analytics model"""
    total_ids_issued: int
    pending_approvals: int
    rejected_photos: int
    recent_submissions: int

@router.get('/analytics/ids', response_model=IDAnalytics)
async def get_id_analytics(
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Get Digital ID analytics.
    
    Available to: Admin only
    """
    total_ids_issued = await db.digital_ids.count_documents({'is_active': True})
    pending_approvals = await db.digital_ids.count_documents({'photo_status': 'pending'})
    rejected_photos = await db.digital_ids.count_documents({'photo_status': 'rejected'})
    
    # Recent submissions (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_submissions = await db.digital_ids.count_documents({
        'updated_at': {'$gte': seven_days_ago},
        'submitted_photo_url': {'$ne': None}
    })
    
    return {
        'total_ids_issued': total_ids_issued,
        'pending_approvals': pending_approvals,
        'rejected_photos': rejected_photos,
        'recent_submissions': recent_submissions
    }


# ============================================
# PHASE 2: LOCATION MANAGEMENT
# ============================================

@router.post('/locations', response_model=Location)
async def create_location(
    location_data: LocationCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Create a new location.
    
    Available to: Admin only
    """
    new_location = location_data.dict()
    new_location['created_at'] = datetime.utcnow()
    new_location['updated_at'] = datetime.utcnow()
    new_location['is_active'] = True
    
    result = await db.locations.insert_one(new_location)
    new_location['_id'] = str(result.inserted_id)
    
    return new_location


@router.put('/locations/{location_id}', response_model=Location)
async def update_location(
    location_id: str,
    location_data: LocationCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Update an existing location.
    
    Available to: Admin only
    """
    location = await db.locations.find_one({'_id': ObjectId(location_id)})
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = location_data.dict()
    update_data['updated_at'] = datetime.utcnow()
    
    await db.locations.update_one(
        {'_id': ObjectId(location_id)},
        {'$set': update_data}
    )
    
    location.update(update_data)
    location['_id'] = str(location['_id'])
    return location


@router.delete('/locations/{location_id}')
async def delete_location(
    location_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Deactivate a location (soft delete).
    
    Available to: Admin only
    """
    location = await db.locations.find_one({'_id': ObjectId(location_id)})
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    await db.locations.update_one(
        {'_id': ObjectId(location_id)},
        {'$set': {'is_active': False, 'updated_at': datetime.utcnow()}}
    )
    
    return {"message": "Location deactivated successfully"}


@router.get('/locations/all', response_model=List[Location])
async def get_all_locations(
    include_inactive: bool = False,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Get all locations including inactive ones.
    
    Available to: Admin only
    """
    query = {} if include_inactive else {'is_active': True}
    locations = await db.locations.find(query).to_list(length=100)
    
    for loc in locations:
        loc['_id'] = str(loc['_id'])
    
    return locations


# ============================================
# PHASE 4: DIGITAL ID MANAGEMENT
# ============================================

@router.get('/ids/all')
async def get_all_ids(
    status: Optional[str] = None,
    role: Optional[str] = None,
    approval_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Get all digital IDs with filters.
    
    Available to: Admin only
    """
    query = {}
    
    if status:
        query['is_active'] = (status == 'active')
    
    if approval_status:
        query['photo_status'] = approval_status
    
    # Get IDs
    ids = await db.digital_ids.find(query).skip(skip).limit(limit).to_list(length=limit)
    
    # Enrich with user data
    for id_doc in ids:
        id_doc['_id'] = str(id_doc['_id'])
        user = await db.users.find_one({'_id': ObjectId(id_doc['user_id'])})
        if user:
            id_doc['user'] = {
                'email': user.get('email'),
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'role': user.get('role')
            }
            
            # Filter by role if specified
            if role and user.get('role') != role:
                continue
    
    return ids


@router.get('/ids/pending-approvals')
async def get_pending_approvals(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Get all pending photo approvals.
    
    Available to: Admin, Staff
    """
    pending_ids = await db.digital_ids.find({
        'photo_status': 'pending',
        'submitted_photo_url': {'$ne': None}
    }).to_list(length=100)
    
    # Enrich with user data
    for id_doc in pending_ids:
        id_doc['_id'] = str(id_doc['_id'])
        user = await db.users.find_one({'_id': ObjectId(id_doc['user_id'])})
        if user:
            id_doc['user'] = {
                'email': user.get('email'),
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'role': user.get('role')
            }
    
    return pending_ids


class BulkUploadResult(BaseModel):
    """Bulk upload result model"""
    success_count: int
    error_count: int
    errors: List[Dict[str, str]]
    created_users: List[str]

@router.post('/ids/bulk-upload', response_model=BulkUploadResult)
async def bulk_upload_users_and_ids(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_super_admin),
    db = Depends(get_database)
):
    """
    Bulk upload users and create digital IDs from CSV file.
    
    CSV Format: email, first_name, last_name, role, phone
    
    Available to: Super Admin only
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV"
        )
    
    # Read CSV content
    content = await file.read()
    csv_text = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_text))
    
    success_count = 0
    error_count = 0
    errors = []
    created_users = []
    
    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (row 1 is header)
        try:
            # Validate required fields
            email = row.get('email', '').strip().lower()
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            role = row.get('role', 'student').strip().lower()
            phone = row.get('phone', '').strip()
            
            if not email or not first_name or not last_name:
                errors.append({
                    'row': str(row_num),
                    'error': 'Missing required fields (email, first_name, last_name)'
                })
                error_count += 1
                continue
            
            # Check if user exists
            existing_user = await db.users.find_one({'email': email})
            if existing_user:
                errors.append({
                    'row': str(row_num),
                    'error': f'User with email {email} already exists'
                })
                error_count += 1
                continue
            
            # Validate role
            valid_roles = ['student', 'parent', 'staff', 'admin']
            if role not in valid_roles:
                role = 'student'  # Default to student
            
            # Create user with default password (they should change it)
            default_password = 'ChangeMe123!'  # Must meet password requirements
            from app.services.auth_service import AuthService
            auth_service = AuthService(db)
            
            user = await auth_service.register_user(
                email=email,
                password=default_password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                phone=phone if phone else None
            )
            
            # Create digital ID
            user_id = str(user['_id'])
            timestamp = int(datetime.utcnow().timestamp())
            qr_code = f"AISJ:{user_id}:{timestamp}"
            barcode = f"{timestamp}"
            
            id_data = {
                'user_id': user_id,
                'qr_code': qr_code,
                'barcode': barcode,
                'photo_url': None,
                'photo_status': 'pending',
                'is_active': True,
                'issued_at': datetime.utcnow(),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            await db.digital_ids.insert_one(id_data)
            
            success_count += 1
            created_users.append(f"{first_name} {last_name} ({email})")
            
        except Exception as e:
            errors.append({
                'row': str(row_num),
                'error': str(e)
            })
            error_count += 1
    
    return {
        'success_count': success_count,
        'error_count': error_count,
        'errors': errors,
        'created_users': created_users
    }


@router.post('/ids/issue/{user_id}')
async def manually_issue_id(
    user_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Manually issue a digital ID for a user.
    
    Available to: Admin only
    """
    # Check if user exists
    user = await db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if ID already exists
    existing_id = await db.digital_ids.find_one({'user_id': user_id})
    if existing_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a digital ID"
        )
    
    # Create digital ID
    timestamp = int(datetime.utcnow().timestamp())
    qr_code = f"AISJ:{user_id}:{timestamp}"
    barcode = f"{timestamp}"
    
    id_data = {
        'user_id': user_id,
        'qr_code': qr_code,
        'barcode': barcode,
        'photo_url': user.get('profile_photo_url'),
        'photo_status': 'approved' if user.get('profile_photo_url') else 'pending',
        'is_active': True,
        'issued_at': datetime.utcnow(),
        'issued_by': str(current_user['_id']),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    result = await db.digital_ids.insert_one(id_data)
    id_data['_id'] = str(result.inserted_id)
    
    return {"message": "Digital ID issued successfully", "id": id_data}


@router.put('/ids/{id_id}/toggle-status')
async def toggle_id_status(
    id_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Activate or deactivate a digital ID.
    
    Available to: Admin only
    """
    digital_id = await db.digital_ids.find_one({'_id': ObjectId(id_id)})
    if not digital_id:
        raise HTTPException(status_code=404, detail="Digital ID not found")
    
    new_status = not digital_id.get('is_active', True)
    
    await db.digital_ids.update_one(
        {'_id': ObjectId(id_id)},
        {'$set': {
            'is_active': new_status,
            'updated_at': datetime.utcnow()
        }}
    )
    
    return {
        "message": f"Digital ID {'activated' if new_status else 'deactivated'} successfully",
        "is_active": new_status
    }


@router.delete('/ids/{id_id}')
async def delete_id(
    id_id: str,
    current_user: dict = Depends(require_super_admin),
    db = Depends(get_database)
):
    """
    Permanently delete a digital ID.
    
    Available to: Super Admin only
    """
    result = await db.digital_ids.delete_one({'_id': ObjectId(id_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Digital ID not found")
    
    return {"message": "Digital ID deleted successfully"}
