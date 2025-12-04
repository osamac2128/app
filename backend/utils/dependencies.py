from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from utils.auth import decode_access_token
from app.core.database import get_database
from bson import ObjectId

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db = Depends(get_database)):
    """Dependency to get the current authenticated user."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    user_id: str = payload.get('sub')
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    # Fetch user from database
    user = await db.users.find_one({'_id': ObjectId(user_id)})
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found',
        )
    
    # Convert ObjectId to string for JSON serialization
    user['_id'] = str(user['_id'])
    
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Dependency to get current active user only."""
    if current_user.get('status') != 'active':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Inactive user account'
        )
    return current_user

def require_role(*allowed_roles: str):
    """Dependency factory to require specific roles."""
    async def role_checker(current_user: dict = Depends(get_current_active_user)):
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Insufficient permissions'
            )
        return current_user
    return role_checker
