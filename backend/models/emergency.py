from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .users import DivisionType

# Enums
class EmergencyType(str, Enum):
    """Types of emergency alerts"""
    LOCKDOWN = "lockdown"  # Secure, shelter-in-place
    LOCKDOWN_SECURE = "lockdown_secure"  # Lock doors, continue activities
    LOCKOUT = "lockout"  # Threat outside building
    FIRE = "fire"  # Evacuation
    FIRE_DRILL = "fire_drill"
    MEDICAL = "medical"
    WEATHER = "weather"  # Tornado, hurricane
    TORNADO = "tornado"
    TORNADO_DRILL = "tornado_drill"
    EARTHQUAKE = "earthquake"
    EARTHQUAKE_DRILL = "earthquake_drill"
    HAZMAT = "hazmat"  # Chemical/environmental
    POLICE_ACTIVITY = "police_activity"
    EVACUATION = "evacuation"  # General evacuation
    SHELTER_IN_PLACE = "shelter_in_place"
    ALL_CLEAR = "all_clear"
    DRILL = "drill"  # General drill
    OTHER = "other"

class SeverityLevel(str, Enum):
    """Severity levels"""
    INFO = "info"  # All-clear, announcements
    LOW = "low"  # Minor incidents, drills
    MEDIUM = "medium"  # Requires attention
    HIGH = "high"  # Serious emergency
    CRITICAL = "critical"  # Life-threatening

class CheckinStatus(str, Enum):
    """Check-in status options"""
    SAFE = "safe"
    SAFE_WITH_INJURIES = "safe_with_injuries"
    NEED_HELP = "need_help"
    NEED_MEDICAL = "need_medical"
    MISSING = "missing"
    NOT_CHECKED_IN = "not_checked_in"

class AlertScope(str, Enum):
    """Alert distribution scope"""
    SCHOOL_WIDE = "school_wide"
    BUILDING = "building"
    FLOOR = "floor"
    WING = "wing"
    CLASSROOM = "classroom"
    CUSTOM = "custom"

class DrillType(str, Enum):
    """Types of emergency drills"""
    FIRE = "fire"
    LOCKDOWN = "lockdown"
    TORNADO = "tornado"
    EARTHQUAKE = "earthquake"
    EVACUATION = "evacuation"
    CUSTOM = "custom"

# Emergency Alert Models
class EmergencyAlert(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    type: EmergencyType
    title: str
    message: str
    severity: SeverityLevel
    instructions: Optional[str] = None
    is_drill: bool = False
    triggered_by: str  # Reference to User
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None  # Reference to User
    resolution_notes: Optional[str] = None
    affected_buildings: Optional[List[str]] = None
    affected_divisions: Optional[List[DivisionType]] = None
    parent_alert_id: Optional[str] = None  # Reference to EmergencyAlert (for updates)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class EmergencyAlertCreate(BaseModel):
    type: EmergencyType
    title: str
    message: str
    severity: SeverityLevel
    instructions: Optional[str] = None
    is_drill: bool = False
    triggered_by: str
    affected_buildings: Optional[List[str]] = None
    affected_divisions: Optional[List[DivisionType]] = None

    class Config:
        use_enum_values = True

class EmergencyAlertUpdate(BaseModel):
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None

# Emergency Check-in Models (for accountability during emergencies)
class EmergencyCheckIn(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    alert_id: str  # Reference to EmergencyAlert
    user_id: str  # Reference to User
    status: CheckinStatus = CheckinStatus.UNACCOUNTED
    location: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    checked_by: Optional[str] = None  # Reference to User
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class EmergencyCheckInCreate(BaseModel):
    alert_id: str
    user_id: str
    status: CheckinStatus = CheckinStatus.UNACCOUNTED
    location: Optional[str] = None

    class Config:
        use_enum_values = True

class EmergencyCheckInUpdate(BaseModel):
    status: Optional[CheckinStatus] = None
    location: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    checked_by: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        use_enum_values = True
