from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .users import DivisionType

# Enums
class EmergencyType(str, Enum):
    LOCKDOWN = "lockdown"
    FIRE = "fire"
    SHELTER = "shelter"
    HOLD = "hold"
    ALL_CLEAR = "all_clear"
    DRILL = "drill"
    MEDICAL = "medical"
    WEATHER = "weather"

class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CheckinStatus(str, Enum):
    SAFE = "safe"
    NEED_HELP = "need_help"
    UNACCOUNTED = "unaccounted"

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
