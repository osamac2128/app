from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, date, time
from enum import Enum

# Enums
class VisitorPurpose(str, Enum):
    MEETING = "meeting"
    DELIVERY = "delivery"
    CONTRACTOR = "contractor"
    PARENT = "parent"
    EVENT = "event"
    INTERVIEW = "interview"
    OTHER = "other"

class IDDocumentType(str, Enum):
    PASSPORT = "passport"
    IQAMA = "iqama"
    NATIONAL_ID = "national_id"
    DRIVERS_LICENSE = "drivers_license"
    OTHER = "other"

# Visitor Models
class Visitor(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    id_type: Optional[IDDocumentType] = None
    id_number: Optional[str] = None
    id_document_url: Optional[str] = None  # base64 or URL
    photo_url: Optional[str] = None  # base64 or URL
    company: Optional[str] = None
    is_on_watchlist: bool = False
    watchlist_reason: Optional[str] = None
    watchlist_added_by: Optional[str] = None  # Reference to User
    watchlist_added_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class VisitorCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    id_type: Optional[IDDocumentType] = None
    id_number: Optional[str] = None
    id_document_url: Optional[str] = None
    photo_url: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        use_enum_values = True

class VisitorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    id_type: Optional[IDDocumentType] = None
    id_number: Optional[str] = None
    company: Optional[str] = None
    is_on_watchlist: Optional[bool] = None
    watchlist_reason: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        use_enum_values = True

# Visitor Log Models (check-in/check-out)
class VisitorLog(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    visitor_id: str  # Reference to Visitor
    purpose: VisitorPurpose
    purpose_detail: Optional[str] = None
    host_user_id: Optional[str] = None  # Reference to User
    host_notified_at: Optional[datetime] = None
    badge_number: Optional[str] = None
    checked_in_at: datetime = Field(default_factory=datetime.utcnow)
    checked_out_at: Optional[datetime] = None
    checked_in_by: Optional[str] = None  # Reference to User
    checked_out_by: Optional[str] = None  # Reference to User
    destination: Optional[str] = None
    is_pre_registered: bool = False
    pre_registration_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class VisitorLogCreate(BaseModel):
    visitor_id: str
    purpose: VisitorPurpose
    purpose_detail: Optional[str] = None
    host_user_id: Optional[str] = None
    badge_number: Optional[str] = None
    destination: Optional[str] = None
    is_pre_registered: bool = False
    pre_registration_id: Optional[str] = None
    checked_in_by: Optional[str] = None

    class Config:
        use_enum_values = True

class VisitorLogUpdate(BaseModel):
    checked_out_at: Optional[datetime] = None
    checked_out_by: Optional[str] = None
    notes: Optional[str] = None

# Visitor Pre-registration Models
class VisitorPreRegistration(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    visitor_email: Optional[EmailStr] = None
    visitor_first_name: str
    visitor_last_name: str
    visitor_phone: Optional[str] = None
    visitor_company: Optional[str] = None
    purpose: VisitorPurpose
    purpose_detail: Optional[str] = None
    host_user_id: str  # Reference to User
    expected_date: str  # Store as ISO date string
    expected_time: Optional[str] = None  # Store as "HH:MM:SS"
    access_code: Optional[str] = None  # Unique access code
    is_used: bool = False
    used_at: Optional[datetime] = None
    created_by: str  # Reference to User
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class VisitorPreRegistrationCreate(BaseModel):
    visitor_email: Optional[EmailStr] = None
    visitor_first_name: str
    visitor_last_name: str
    visitor_phone: Optional[str] = None
    visitor_company: Optional[str] = None
    purpose: VisitorPurpose
    purpose_detail: Optional[str] = None
    host_user_id: str
    expected_date: str
    expected_time: Optional[str] = None
    created_by: str

    class Config:
        use_enum_values = True

class VisitorPreRegistrationUpdate(BaseModel):
    is_used: Optional[bool] = None
    used_at: Optional[datetime] = None
