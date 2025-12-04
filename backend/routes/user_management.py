"""User Management API - Admin CRUD operations for users"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_database
from utils.dependencies import require_role
from models.users import UserRole
from pydantic import BaseModel, EmailStr
from bson import ObjectId
import bcrypt

router = APIRouter(prefix='/admin/users', tags=['User Management'])


class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    phone: Optional[str] = None
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None


class PasswordReset(BaseModel):
    new_password: str


@router.get('', response_model=List[UserResponse])
async def get_all_users(
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Get all users with optional filters.
    
    Available to: Admin only
    """
    query = {}
    
    if role:
        query['role'] = role
    
    if status:
        query['status'] = status
    
    if search:
        query['$or'] = [
            {'first_name': {'$regex': search, '$options': 'i'}},
            {'last_name': {'$regex': search, '$options': 'i'}},
            {'email': {'$regex': search, '$options': 'i'}}
        ]
    
    users = await db.users.find(query).skip(skip).limit(limit).to_list(length=limit)
    
    result = []
    for user in users:
        result.append({
            'id': str(user['_id']),
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'email': user['email'],
            'role': user['role'],
            'phone': user.get('phone'),
            'status': user.get('status', 'active'),
            'created_at': user.get('created_at', datetime.utcnow()),
            'last_login_at': user.get('last_login_at')
        })
    
    return result


@router.get('/{user_id}', response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Get specific user details.
    
    Available to: Admin only
    """
    user = await db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        'id': str(user['_id']),
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'email': user['email'],
        'role': user['role'],
        'phone': user.get('phone'),
        'status': user.get('status', 'active'),
        'created_at': user.get('created_at', datetime.utcnow()),
        'last_login_at': user.get('last_login_at')
    }


@router.put('/{user_id}', response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Update user information.
    
    Available to: Admin only
    """
    user = await db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items() if v is not None}
    
    if update_data:
        update_data['updated_at'] = datetime.utcnow()
        
        await db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
    
    updated_user = await db.users.find_one({'_id': ObjectId(user_id)})
    
    return {
        'id': str(updated_user['_id']),
        'first_name': updated_user['first_name'],
        'last_name': updated_user['last_name'],
        'email': updated_user['email'],
        'role': updated_user['role'],
        'phone': updated_user.get('phone'),
        'status': updated_user.get('status', 'active'),
        'created_at': updated_user.get('created_at', datetime.utcnow()),
        'last_login_at': updated_user.get('last_login_at')
    }


@router.post('/{user_id}/deactivate')
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Deactivate a user account.
    
    Available to: Admin only
    """
    user = await db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deactivating self
    if str(user['_id']) == str(current_user['_id']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    await db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'status': 'inactive', 'updated_at': datetime.utcnow()}}
    )
    
    # Also deactivate their digital ID
    await db.digital_ids.update_one(
        {'user_id': user_id},
        {'$set': {'is_active': False, 'updated_at': datetime.utcnow()}}
    )
    
    return {"message": "User deactivated successfully"}


@router.post('/{user_id}/activate')
async def activate_user(
    user_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Activate a user account.
    
    Available to: Admin only
    """
    user = await db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'status': 'active', 'updated_at': datetime.utcnow()}}
    )
    
    # Also activate their digital ID
    await db.digital_ids.update_one(
        {'user_id': user_id},
        {'$set': {'is_active': True, 'updated_at': datetime.utcnow()}}
    )
    
    return {"message": "User activated successfully"}


@router.post('/{user_id}/reset-password')
async def reset_user_password(
    user_id: str,
    password_data: PasswordReset,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Reset a user's password.
    
    Available to: Admin only
    """
    user = await db.users.find_one({'_id': ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash the new password
    hashed_password = bcrypt.hashpw(
        password_data.new_password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    await db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {
            'password_hash': hashed_password,
            'updated_at': datetime.utcnow()
        }}
    )
    
    return {"message": "Password reset successfully"}


@router.get('/stats/summary')
async def get_user_statistics(
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Get user statistics summary.
    
    Available to: Admin only
    """
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({'status': 'active'})
    inactive_users = await db.users.count_documents({'status': 'inactive'})
    
    users_by_role = {}
    for role in ['student', 'parent', 'staff', 'admin']:
        count = await db.users.count_documents({'role': role, 'status': 'active'})
        users_by_role[role] = count
    
    # Recent registrations (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_registrations = await db.users.count_documents({
        'created_at': {'$gte': seven_days_ago}
    })
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'users_by_role': users_by_role,
        'recent_registrations': recent_registrations
    }
