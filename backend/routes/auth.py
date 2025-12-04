from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from app.core.database import get_database
from utils.auth import verify_password, get_password_hash, create_access_token
from utils.dependencies import get_current_active_user
from models.users import UserRole, UserStatus, UserCreate, User, UserUpdate
from bson import ObjectId
import re

router = APIRouter(prefix='/auth', tags=['Authentication'])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole
    phone: str = Field(default=None, max_length=20)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

    class Config:
        use_enum_values = True

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: dict

@router.post('/register', response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new user."""
    db = get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({'email': request.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email already registered'
        )
    
    # Create new user
    password_hash = get_password_hash(request.password)
    
    user_data = {
        'email': request.email.lower(),
        'password_hash': password_hash,
        'first_name': request.first_name,
        'last_name': request.last_name,
        'role': request.role,
        'phone': request.phone,
        'profile_photo_url': None,
        'status': UserStatus.ACTIVE.value,
        'device_tokens': [],
        'notification_preferences': {},
        'last_login_at': None,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token(data={'sub': user_id, 'role': request.role})
    
    # Return user data without password
    user_data['_id'] = user_id
    user_data.pop('password_hash')
    
    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user': user_data
    }

@router.post('/login', response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    db = get_database()
    
    # Find user by email
    user = await db.users.find_one({'email': request.email.lower()})
    
    if not user or not verify_password(request.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    
    # Check if user is active
    if user.get('status') != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Account is inactive or suspended'
        )
    
    # Update last login
    await db.users.update_one(
        {'_id': user['_id']},
        {'$set': {'last_login_at': datetime.utcnow()}}
    )
    
    # Create access token
    user_id = str(user['_id'])
    access_token = create_access_token(data={'sub': user_id, 'role': user['role']})
    
    # Return user data without password
    user['_id'] = user_id
    user.pop('password_hash')
    
    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user': user
    }

@router.get('/me')
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current user information."""
    # Remove sensitive data
    user_data = current_user.copy()
    user_data.pop('password_hash', None)
    return user_data

@router.post('/logout')
async def logout(current_user: dict = Depends(get_current_active_user)):
    """Logout current user (client should delete token)."""
    # In a JWT system, logout is handled client-side by deleting the token
    # Optionally, you could maintain a token blacklist
    return {'message': 'Successfully logged out'}

@router.put('/me', response_model=dict)
async def update_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update current user profile."""
    db = get_database()
    
    # Filter out None values
    update_fields = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
    
    if not update_fields:
        return current_user

    update_fields['updated_at'] = datetime.utcnow()

    await db.users.update_one(
        {'_id': ObjectId(current_user['_id'])},
        {'$set': update_fields}
    )
    
    # Fetch updated user
    updated_user = await db.users.find_one({'_id': ObjectId(current_user['_id'])})
    updated_user['_id'] = str(updated_user['_id'])
    updated_user.pop('password_hash', None)
    
    return updated_user
