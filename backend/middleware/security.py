"""Security middleware and utilities"""

from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from typing import Dict, Optional
import re


# ============================================
# PASSWORD STRENGTH VALIDATION
# ============================================

class PasswordValidator:
    """
    Password strength validator.
    """
    
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
    SPECIAL_CHARS = r"!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @classmethod
    def validate(cls, password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Returns: (is_valid, error_message)
        """
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters long"
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if cls.REQUIRE_SPECIAL and not re.search(f"[{re.escape(cls.SPECIAL_CHARS)}]", password):
            return False, f"Password must contain at least one special character: {cls.SPECIAL_CHARS}"
        
        # Check for common patterns
        common_patterns = [
            r'(.)\1{2,}',  # Repeated characters
            r'12345',
            r'password',
            r'qwerty',
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                return False, "Password contains common patterns or sequences"
        
        return True, None


# ============================================
# ACCOUNT LOCKOUT TRACKER
# ============================================

class AccountLockoutTracker:
    """
    Track failed login attempts and lockout accounts.
    """
    
    def __init__(self):
        # Store: {email: {'count': int, 'locked_until': datetime, 'attempts': [datetime]}}
        self.failed_attempts: Dict[str, dict] = {}
        self.max_attempts = 5
        self.lockout_duration = 900  # 15 minutes in seconds
        self.attempt_window = 300  # 5 minutes
    
    def record_failed_attempt(self, email: str) -> dict:
        """
        Record a failed login attempt.
        
        Returns: {
            'locked': bool,
            'attempts_remaining': int,
            'locked_until': Optional[datetime]
        }
        """
        now = datetime.utcnow()
        
        if email not in self.failed_attempts:
            self.failed_attempts[email] = {
                'count': 0,
                'attempts': [],
                'locked_until': None
            }
        
        account = self.failed_attempts[email]
        
        # Check if currently locked
        if account['locked_until'] and now < account['locked_until']:
            return {
                'locked': True,
                'attempts_remaining': 0,
                'locked_until': account['locked_until']
            }
        
        # Clear old attempts outside the window
        window_start = now - timedelta(seconds=self.attempt_window)
        account['attempts'] = [
            attempt for attempt in account['attempts']
            if attempt > window_start
        ]
        
        # Add new attempt
        account['attempts'].append(now)
        account['count'] = len(account['attempts'])
        
        # Check if should be locked
        if account['count'] >= self.max_attempts:
            account['locked_until'] = now + timedelta(seconds=self.lockout_duration)
            return {
                'locked': True,
                'attempts_remaining': 0,
                'locked_until': account['locked_until']
            }
        
        return {
            'locked': False,
            'attempts_remaining': self.max_attempts - account['count'],
            'locked_until': None
        }
    
    def is_locked(self, email: str) -> tuple[bool, Optional[datetime]]:
        """
        Check if account is currently locked.
        
        Returns: (is_locked, locked_until)
        """
        if email not in self.failed_attempts:
            return False, None
        
        account = self.failed_attempts[email]
        
        if account['locked_until'] and datetime.utcnow() < account['locked_until']:
            return True, account['locked_until']
        
        return False, None
    
    def reset_attempts(self, email: str):
        """
        Reset failed attempts after successful login.
        """
        if email in self.failed_attempts:
            del self.failed_attempts[email]


# Global lockout tracker instance
lockout_tracker = AccountLockoutTracker()


# ============================================
# INPUT SANITIZATION
# ============================================

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize user input string.
    """
    if not isinstance(value, str):
        return ""
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Trim to max length
    value = value[:max_length]
    
    # Strip leading/trailing whitespace
    value = value.strip()
    
    return value


def sanitize_email(email: str) -> str:
    """
    Sanitize and normalize email address.
    """
    email = sanitize_string(email, 255)
    email = email.lower()
    return email
