"""Authentication service for user authentication and management"""

from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.user_repository import UserRepository
from app.core.exceptions import (
    ValidationException,
    UnauthorizedException,
    ConflictException,
    NotFoundException
)
from utils.auth import verify_password, get_password_hash, create_access_token
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and user management operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize auth service.

        Args:
            db: Motor database instance
        """
        self.db = db
        self.user_repo = UserRepository(db)

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            email: User's email address
            password: Plain text password
            first_name: User's first name
            last_name: User's last name
            role: User role (student, parent, staff, admin)
            phone: Optional phone number

        Returns:
            User document without password hash

        Raises:
            ConflictException: If email already exists
            ValidationException: If validation fails
        """
        # Validate email format
        email = email.lower().strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationException("Invalid email format")

        # Validate password strength
        self._validate_password(password)

        # Check if email already exists
        if await self.user_repo.email_exists(email):
            raise ConflictException("Email already registered")

        # Validate role
        valid_roles = ['student', 'parent', 'staff', 'admin']
        if role not in valid_roles:
            raise ValidationException(f"Invalid role. Must be one of: {', '.join(valid_roles)}")

        # Hash password
        password_hash = get_password_hash(password)

        # Create user document
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'role': role,
            'phone': phone,
            'profile_photo_url': None,
            'status': 'active',
            'device_tokens': [],
            'notification_preferences': {},
            'last_login_at': None,
        }

        try:
            user_id = await self.user_repo.insert_one(user_data)
            logger.info(f"User registered successfully: {email} (role: {role})")

            # Return user without password
            user_data['_id'] = user_id
            user_data.pop('password_hash')
            return user_data

        except Exception as e:
            logger.error(f"Error registering user {email}: {e}")
            raise

    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            User document without password hash

        Raises:
            UnauthorizedException: If credentials are invalid or account is inactive
        """
        email = email.lower().strip()

        # Find user by email
        user = await self.user_repo.find_by_email(email)

        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise UnauthorizedException("Invalid email or password")

        # Verify password
        if not verify_password(password, user['password_hash']):
            logger.warning(f"Failed login attempt for user: {email}")
            raise UnauthorizedException("Invalid email or password")

        # Check if account is active
        if user.get('status') != 'active':
            logger.warning(f"Login attempt for inactive account: {email}")
            raise UnauthorizedException("Account is inactive or suspended")

        # Update last login timestamp
        await self.user_repo.update_last_login(user['_id'])

        logger.info(f"User authenticated successfully: {email}")

        # Return user without password
        user.pop('password_hash')
        return user

    async def create_access_token_for_user(self, user: Dict[str, Any]) -> str:
        """
        Create an access token for a user.

        Args:
            user: User document

        Returns:
            JWT access token
        """
        token_data = {
            'sub': user['_id'],
            'role': user['role'],
            'email': user.get('email')
        }
        return create_access_token(token_data)

    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User document without password hash

        Raises:
            NotFoundException: If user not found
        """
        user = await self.user_repo.find_by_id(user_id)

        if not user:
            raise NotFoundException("User not found")

        # Remove sensitive data
        user.pop('password_hash', None)
        return user

    async def update_user_profile(
        self,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user profile information.

        Args:
            user_id: User ID
            update_data: Fields to update

        Returns:
            Updated user document without password hash

        Raises:
            NotFoundException: If user not found
            ValidationException: If validation fails
        """
        # Verify user exists
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        # Filter allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'phone',
            'profile_photo_url', 'notification_preferences'
        ]
        filtered_data = {
            k: v for k, v in update_data.items()
            if k in allowed_fields and v is not None
        }

        if not filtered_data:
            return user

        # Update user
        await self.user_repo.update_one(user_id, filtered_data)
        logger.info(f"User profile updated: {user_id}")

        # Return updated user
        updated_user = await self.user_repo.find_by_id(user_id)
        updated_user.pop('password_hash', None)
        return updated_user

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            NotFoundException: If user not found
            UnauthorizedException: If old password is incorrect
            ValidationException: If new password is invalid
        """
        # Get user with password hash
        user = await self.user_repo.collection.find_one({"_id": user_id})
        if not user:
            raise NotFoundException("User not found")

        # Verify old password
        if not verify_password(old_password, user['password_hash']):
            raise UnauthorizedException("Current password is incorrect")

        # Validate new password
        self._validate_password(new_password)

        # Hash and update password
        new_password_hash = get_password_hash(new_password)
        await self.user_repo.update_one(user_id, {'password_hash': new_password_hash})

        logger.info(f"Password changed for user: {user_id}")
        return True

    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            True if deactivated successfully

        Raises:
            NotFoundException: If user not found
        """
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")

        result = await self.user_repo.deactivate_user(user_id)
        logger.info(f"User deactivated: {user_id}")
        return result

    def _validate_password(self, password: str) -> None:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Raises:
            ValidationException: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValidationException('Password must be at least 8 characters long')

        if not re.search(r'[A-Z]', password):
            raise ValidationException('Password must contain at least one uppercase letter')

        if not re.search(r'[a-z]', password):
            raise ValidationException('Password must contain at least one lowercase letter')

        if not re.search(r'[0-9]', password):
            raise ValidationException('Password must contain at least one number')
