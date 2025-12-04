"""Authentication routes"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.core.database import get_database
from app.services.auth_service import AuthService
from app.core.exceptions import (
    ValidationException,
    UnauthorizedException,
    ConflictException,
    NotFoundException
)
from utils.dependencies import get_current_active_user
from models.users import UserRole, UserUpdate
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix='/auth', tags=['Authentication'])


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request model"""
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole
    phone: Optional[str] = Field(default=None, max_length=20)

    class Config:
        use_enum_values = True


class AuthResponse(BaseModel):
    """Authentication response model"""
    access_token: str
    token_type: str = 'bearer'
    user: dict


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    old_password: str
    new_password: str = Field(min_length=8)


# Dependency to get auth service
async def get_auth_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthService:
    """Get auth service instance"""
    return AuthService(db)


# Routes
@router.post('/register', response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.

    Creates a new user account and returns an access token.

    Args:
        request: Registration details
        auth_service: Auth service instance

    Returns:
        Access token and user data

    Raises:
        ConflictException: If email already registered
        ValidationException: If validation fails
    """
    # Restrict admin role to specific emails only
    SUPER_ADMIN_EMAILS = ['osama.chaudhry@gmail.com', 'ochaudhry@aisj.edu.sa']
    
    if request.role == UserRole.ADMIN:
        if request.email.lower() not in SUPER_ADMIN_EMAILS:
            raise ValidationException(
                "Admin role is restricted. Only authorized super administrators can register with admin privileges."
            )
    
    # Register user through service
    user = await auth_service.register_user(
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        phone=request.phone
    )

    # Create access token
    access_token = await auth_service.create_access_token_for_user(user)

    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user': user
    }


@router.post('/login', response_model=AuthResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email and password.

    Authenticates user credentials and returns an access token.

    Args:
        request: Login credentials
        auth_service: Auth service instance

    Returns:
        Access token and user data

    Raises:
        UnauthorizedException: If credentials are invalid or account is inactive
    """
    # Authenticate user through service
    user = await auth_service.authenticate_user(
        email=request.email,
        password=request.password
    )

    # Create access token
    access_token = await auth_service.create_access_token_for_user(user)

    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user': user
    }


@router.get('/me')
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current user information.

    Returns the currently authenticated user's profile.

    Args:
        current_user: Current authenticated user from token
        auth_service: Auth service instance

    Returns:
        User profile data
    """
    return await auth_service.get_user_by_id(current_user['_id'])


@router.post('/logout')
async def logout(current_user: dict = Depends(get_current_active_user)):
    """
    Logout current user.

    In a JWT system, logout is handled client-side by deleting the token.
    This endpoint exists for API consistency.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    return {'message': 'Successfully logged out'}


@router.put('/me', response_model=dict)
async def update_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update current user profile.

    Updates the authenticated user's profile information.

    Args:
        update_data: Fields to update
        current_user: Current authenticated user
        auth_service: Auth service instance

    Returns:
        Updated user profile

    Raises:
        ValidationException: If validation fails
    """
    return await auth_service.update_user_profile(
        user_id=current_user['_id'],
        update_data=update_data.dict(exclude_unset=True)
    )


@router.post('/change-password')
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user password.

    Updates the authenticated user's password.

    Args:
        request: Password change details
        current_user: Current authenticated user
        auth_service: Auth service instance

    Returns:
        Success message

    Raises:
        UnauthorizedException: If old password is incorrect
        ValidationException: If new password is invalid
    """
    await auth_service.change_password(
        user_id=current_user['_id'],
        old_password=request.old_password,
        new_password=request.new_password
    )

    return {'message': 'Password changed successfully'}
