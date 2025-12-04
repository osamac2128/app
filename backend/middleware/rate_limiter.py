"""Rate Limiting Middleware for API endpoints"""

from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from typing import Dict, Tuple
import time


class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    For production, use Redis for distributed rate limiting.
    """
    
    def __init__(self):
        # Store: {identifier: [(timestamp, count)]}
        self.requests: Dict[str, list] = {}
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        self.last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove entries older than 1 hour"""
        if time.time() - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff = datetime.utcnow() - timedelta(hours=1)
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                (ts, count) for ts, count in self.requests[identifier]
                if ts > cutoff
            ]
            if not self.requests[identifier]:
                del self.requests[identifier]
        
        self.last_cleanup = time.time()
    
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Check if request should be allowed.
        
        Args:
            identifier: Unique identifier (IP, user_id, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            (is_allowed, retry_after_seconds)
        """
        self._cleanup_old_entries()
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Filter requests within the window
        recent_requests = [
            (ts, count) for ts, count in self.requests[identifier]
            if ts > window_start
        ]
        
        # Count total requests in window
        total_requests = sum(count for _, count in recent_requests)
        
        if total_requests >= max_requests:
            # Calculate retry_after based on oldest request in window
            if recent_requests:
                oldest_request = min(ts for ts, _ in recent_requests)
                retry_after = int((oldest_request - window_start).total_seconds())
                return False, max(retry_after, 1)
            return False, window_seconds
        
        # Add this request
        self.requests[identifier] = recent_requests + [(now, 1)]
        return True, 0


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit configurations
RATE_LIMITS = {
    'login': (5, 300),  # 5 requests per 5 minutes
    'register': (3, 3600),  # 3 requests per hour
    'password_reset': (3, 3600),  # 3 requests per hour
    'pass_request': (10, 300),  # 10 pass requests per 5 minutes
    'api_default': (100, 60),  # 100 requests per minute
}


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.
    
    Apply different limits based on endpoint.
    """
    # Skip rate limiting for health checks
    if request.url.path in ['/api/health', '/api/', '/docs', '/redoc']:
        return await call_next(request)
    
    # Determine identifier (IP or user ID)
    identifier = request.client.host
    
    # Check if user is authenticated
    auth_header = request.headers.get('authorization', '')
    if auth_header.startswith('Bearer '):
        # In production, decode token to get user_id
        # For now, use IP + 'auth' to differentiate
        identifier = f"{identifier}_auth"
    
    # Determine rate limit based on endpoint
    path = request.url.path
    
    if '/login' in path:
        max_requests, window = RATE_LIMITS['login']
    elif '/register' in path:
        max_requests, window = RATE_LIMITS['register']
    elif '/reset-password' in path or '/forgot-password' in path:
        max_requests, window = RATE_LIMITS['password_reset']
    elif '/passes/request' in path:
        max_requests, window = RATE_LIMITS['pass_request']
    else:
        max_requests, window = RATE_LIMITS['api_default']
    
    # Check rate limit
    is_allowed, retry_after = rate_limiter.check_rate_limit(
        identifier, max_requests, window
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
    
    response = await call_next(request)
    return response
