from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    STAFF = "staff"
    ADMIN = "admin"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class DivisionType(str, Enum):
    ES = "ES"  # Elementary School
    MS = "MS"  # Middle School
    HS = "HS"  # High School

class RelationshipType(str, Enum):
    MOTHER = "mother"
    FATHER = "father"
    GUARDIAN = "guardian"
    OTHER = "other"

# User Models
class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    password_hash: str
    first_name: str
    last_name: str
    role: UserRole
    phone: Optional[str] = None
    profile_photo_url: Optional[str] = None  # base64 or URL
    status: UserStatus = UserStatus.ACTIVE
    device_tokens: List[str] = Field(default_factory=list)
    notification_preferences: Dict[str, Any] = Field(default_factory=dict)
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole
    phone: Optional[str] = None
    profile_photo_url: Optional[str] = None

    class Config:
        use_enum_values = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    profile_photo_url: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    status: Optional[UserStatus] = None

    class Config:
        use_enum_values = True

# Student Models
class Student(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  # Reference to User
    student_id: str  # Unique student identifier
    grade: str
    division: DivisionType
    homeroom: Optional[str] = None
    advisor_id: Optional[str] = None  # Reference to User (staff)
    daily_pass_limit: int = 5
    pass_time_limit_minutes: int = 5
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class StudentCreate(BaseModel):
    user_id: str
    student_id: str
    grade: str
    division: DivisionType
    homeroom: Optional[str] = None
    advisor_id: Optional[str] = None
    daily_pass_limit: int = 5
    pass_time_limit_minutes: int = 5

    class Config:
        use_enum_values = True

class StudentUpdate(BaseModel):
    grade: Optional[str] = None
    division: Optional[DivisionType] = None
    homeroom: Optional[str] = None
    advisor_id: Optional[str] = None
    daily_pass_limit: Optional[int] = None
    pass_time_limit_minutes: Optional[int] = None

    class Config:
        use_enum_values = True

# Staff Models
class Staff(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  # Reference to User
    employee_id: str  # Unique employee identifier
    department: Optional[str] = None
    position: Optional[str] = None
    room_number: Optional[str] = None
    can_approve_passes: bool = True
    is_hall_monitor: bool = False
    can_trigger_emergency: bool = False
    can_manage_visitors: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class StaffCreate(BaseModel):
    user_id: str
    employee_id: str
    department: Optional[str] = None
    position: Optional[str] = None
    room_number: Optional[str] = None
    can_approve_passes: bool = True
    is_hall_monitor: bool = False
    can_trigger_emergency: bool = False
    can_manage_visitors: bool = False

class StaffUpdate(BaseModel):
    department: Optional[str] = None
    position: Optional[str] = None
    room_number: Optional[str] = None
    can_approve_passes: Optional[bool] = None
    is_hall_monitor: Optional[bool] = None
    can_trigger_emergency: Optional[bool] = None
    can_manage_visitors: Optional[bool] = None

# Parent-Student Relationship Models
class ParentStudentRelation(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    parent_user_id: str  # Reference to User (parent)
    student_id: str  # Reference to Student
    relationship: RelationshipType
    is_primary: bool = False
    can_pickup: bool = True
    can_receive_alerts: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class ParentStudentRelationCreate(BaseModel):
    parent_user_id: str
    student_id: str
    relationship: RelationshipType
    is_primary: bool = False
    can_pickup: bool = True
    can_receive_alerts: bool = True

    class Config:
        use_enum_values = True
