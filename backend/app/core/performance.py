"""
Performance Optimization Utilities
Database indexes, caching, and query optimization for AISJ Connect.
"""

import logging
from functools import lru_cache
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# In-memory cache for frequently accessed data
_cache: Dict[str, Any] = {}
_cache_timestamps: Dict[str, datetime] = {}


class CacheManager:
    """Simple in-memory cache manager with TTL support."""

    DEFAULT_TTL = 300  # 5 minutes

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get a value from cache if not expired."""
        if key not in _cache:
            return None

        timestamp = _cache_timestamps.get(key)
        if timestamp and datetime.utcnow() - timestamp > timedelta(seconds=CacheManager.DEFAULT_TTL):
            # Expired
            del _cache[key]
            del _cache_timestamps[key]
            return None

        return _cache[key]

    @staticmethod
    def set(key: str, value: Any, ttl: int = None) -> None:
        """Set a value in cache with optional TTL."""
        _cache[key] = value
        _cache_timestamps[key] = datetime.utcnow()

    @staticmethod
    def delete(key: str) -> None:
        """Delete a value from cache."""
        _cache.pop(key, None)
        _cache_timestamps.pop(key, None)

    @staticmethod
    def clear() -> None:
        """Clear all cache."""
        _cache.clear()
        _cache_timestamps.clear()


# Database index definitions for optimal query performance
DATABASE_INDEXES = {
    "users": [
        {"keys": [("email", 1)], "unique": True},
        {"keys": [("role", 1)]},
        {"keys": [("status", 1)]},
        {"keys": [("created_at", -1)]},
    ],
    "digital_ids": [
        {"keys": [("user_id", 1)], "unique": True},
        {"keys": [("qr_code", 1)], "unique": True},
        {"keys": [("barcode", 1)], "unique": True},
        {"keys": [("is_active", 1)]},
        {"keys": [("photo_status", 1)]},
    ],
    "passes": [
        {"keys": [("student_id", 1)]},
        {"keys": [("status", 1)]},
        {"keys": [("created_at", -1)]},
        {"keys": [("student_id", 1), ("status", 1)]},
        {"keys": [("origin_location_id", 1)]},
        {"keys": [("destination_location_id", 1)]},
    ],
    "locations": [
        {"keys": [("name", 1)]},
        {"keys": [("is_active", 1)]},
    ],
    "emergency_alerts": [
        {"keys": [("triggered_at", -1)]},
        {"keys": [("resolved_at", 1)]},
        {"keys": [("type", 1)]},
    ],
    "emergency_checkins": [
        {"keys": [("alert_id", 1)]},
        {"keys": [("user_id", 1)]},
        {"keys": [("alert_id", 1), ("user_id", 1)]},
    ],
    "notifications": [
        {"keys": [("created_at", -1)]},
        {"keys": [("status", 1)]},
        {"keys": [("scheduled_for", 1)]},
        {"keys": [("target_roles", 1)]},
    ],
    "notification_receipts": [
        {"keys": [("notification_id", 1)]},
        {"keys": [("user_id", 1)]},
        {"keys": [("notification_id", 1), ("user_id", 1)]},
    ],
    "visitors": [
        {"keys": [("email", 1)]},
        {"keys": [("phone", 1)]},
        {"keys": [("created_at", -1)]},
    ],
    "visitor_logs": [
        {"keys": [("visitor_id", 1)]},
        {"keys": [("check_in_time", -1)]},
        {"keys": [("check_out_time", 1)]},
    ],
    "id_scan_logs": [
        {"keys": [("digital_id_id", 1)]},
        {"keys": [("scanned_by", 1)]},
        {"keys": [("scanned_at", -1)]},
    ],
    "audit_logs": [
        {"keys": [("created_at", -1)]},
        {"keys": [("user_id", 1)]},
        {"keys": [("action", 1)]},
    ],
}


async def ensure_indexes(db) -> None:
    """Create all database indexes for optimal performance."""
    logger.info("Creating database indexes...")

    for collection_name, indexes in DATABASE_INDEXES.items():
        collection = db[collection_name]
        for index_def in indexes:
            try:
                await collection.create_index(
                    index_def["keys"],
                    unique=index_def.get("unique", False),
                    background=True
                )
            except Exception as e:
                logger.warning(f"Index creation warning for {collection_name}: {e}")

    logger.info("Database indexes created successfully")


# Query optimization helpers
def paginate_query(page: int = 1, per_page: int = 20) -> tuple:
    """Calculate skip and limit for pagination."""
    skip = (page - 1) * per_page
    return skip, per_page


def build_user_filter(
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> dict:
    """Build optimized filter for user queries."""
    filter_dict = {}

    if role:
        filter_dict["role"] = role
    if status:
        filter_dict["status"] = status
    if search:
        filter_dict["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    return filter_dict


def build_pass_filter(
    student_id: Optional[str] = None,
    status: Optional[str] = None,
    location_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> dict:
    """Build optimized filter for pass queries."""
    filter_dict = {}

    if student_id:
        filter_dict["student_id"] = student_id
    if status:
        if isinstance(status, list):
            filter_dict["status"] = {"$in": status}
        else:
            filter_dict["status"] = status
    if location_id:
        filter_dict["$or"] = [
            {"origin_location_id": location_id},
            {"destination_location_id": location_id}
        ]
    if date_from or date_to:
        filter_dict["created_at"] = {}
        if date_from:
            filter_dict["created_at"]["$gte"] = date_from
        if date_to:
            filter_dict["created_at"]["$lte"] = date_to

    return filter_dict


# Cached location lookup
@lru_cache(maxsize=100)
def get_cached_location_names() -> dict:
    """Cache location ID to name mapping."""
    return {}  # Populated on first use


async def warm_location_cache(db) -> None:
    """Pre-load location data into cache."""
    locations = await db.locations.find({}).to_list(length=100)
    location_map = {str(loc["_id"]): loc["name"] for loc in locations}
    CacheManager.set("locations", location_map, ttl=3600)
    logger.info(f"Location cache warmed with {len(locations)} entries")


# Performance monitoring
class PerformanceMonitor:
    """Simple performance monitoring for API endpoints."""

    _metrics: Dict[str, List[float]] = {}

    @classmethod
    def record(cls, endpoint: str, duration_ms: float) -> None:
        """Record endpoint response time."""
        if endpoint not in cls._metrics:
            cls._metrics[endpoint] = []

        # Keep only last 1000 measurements
        if len(cls._metrics[endpoint]) >= 1000:
            cls._metrics[endpoint] = cls._metrics[endpoint][-500:]

        cls._metrics[endpoint].append(duration_ms)

    @classmethod
    def get_stats(cls, endpoint: str = None) -> dict:
        """Get performance statistics."""
        if endpoint:
            times = cls._metrics.get(endpoint, [])
            if not times:
                return {"endpoint": endpoint, "count": 0}
            return {
                "endpoint": endpoint,
                "count": len(times),
                "avg_ms": sum(times) / len(times),
                "min_ms": min(times),
                "max_ms": max(times),
            }

        return {
            endpoint: cls.get_stats(endpoint)
            for endpoint in cls._metrics.keys()
        }
