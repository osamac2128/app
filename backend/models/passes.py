from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, time
from enum import Enum
from .users import DivisionType

# Enums
class LocationType(str, Enum):
    CLASSROOM = "classroom"
    BATHROOM = "bathroom"
    OFFICE = "office"
    LIBRARY = "library"
    GYM = "gym"
    CAFETERIA = "cafeteria"
    NURSE = "nurse"
    COUNSELOR = "counselor"
    OTHER = "other"

class PassStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

# Location Models
class Location(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    building: Optional[str] = None
    floor: Optional[str] = None
    room_number: Optional[str] = None
    type: LocationType
    max_capacity: Optional[int] = None
    requires_approval: bool = False
    default_time_limit_minutes: int = 5
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class LocationCreate(BaseModel):
    name: str
    building: Optional[str] = None
    floor: Optional[str] = None
    room_number: Optional[str] = None
    type: LocationType
    max_capacity: Optional[int] = None
    requires_approval: bool = False
    default_time_limit_minutes: int = 5

    class Config:
        use_enum_values = True

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    room_number: Optional[str] = None
    type: Optional[LocationType] = None
    max_capacity: Optional[int] = None
    requires_approval: Optional[bool] = None
    default_time_limit_minutes: Optional[int] = None
    is_active: Optional[bool] = None

    class Config:
        use_enum_values = True

# Pass Models
class Pass(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    student_id: str  # Reference to Student
    origin_location_id: str  # Reference to Location
    destination_location_id: str  # Reference to Location
    status: PassStatus = PassStatus.PENDING
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None  # Reference to User
    departed_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    time_limit_minutes: int = 5
    is_overtime: bool = False
    overtime_notified_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class PassCreate(BaseModel):
    student_id: str
    origin_location_id: str
    destination_location_id: str
    time_limit_minutes: int = 5
    notes: Optional[str] = None

class PassRequest(BaseModel):
    """API request model for creating a pass (student_id comes from auth)"""
    origin_location_id: str
    destination_location_id: str
    time_limit_minutes: int = 5
    notes: Optional[str] = None

class PassUpdate(BaseModel):
    status: Optional[PassStatus] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    departed_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    is_overtime: Optional[bool] = None
    notes: Optional[str] = None

    class Config:
        use_enum_values = True

# Encounter Group Models (for preventing certain students from having passes at the same time)
class EncounterGroup(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: Optional[str] = None
    student_ids: List[str] = Field(default_factory=list)  # References to Students
    created_by: str  # Reference to User
    reason: Optional[str] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class EncounterGroupCreate(BaseModel):
    name: Optional[str] = None
    student_ids: List[str]
    created_by: str
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None

class EncounterGroupUpdate(BaseModel):
    name: Optional[str] = None
    student_ids: Optional[List[str]] = None
    reason: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None

# No-Fly Time Models (time restrictions when passes cannot be issued)
class NoFlyTime(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    start_time: str  # Store as string "HH:MM:SS"
    end_time: str  # Store as string "HH:MM:SS"
    days_of_week: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])  # 1=Monday, 7=Sunday
    affected_divisions: Optional[List[DivisionType]] = None
    affected_grades: Optional[List[str]] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class NoFlyTimeCreate(BaseModel):
    name: str
    start_time: str
    end_time: str
    days_of_week: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    affected_divisions: Optional[List[DivisionType]] = None
    affected_grades: Optional[List[str]] = None

    class Config:
        use_enum_values = True
