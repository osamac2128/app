from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

# Enums
class PhotoStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ScanPurpose(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    VERIFICATION = "verification"
    LUNCH = "lunch"
    EVENT = "event"

# Digital ID Models
class DigitalID(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  # Reference to User
    qr_code: str  # QR code data (unique)
    barcode: str  # Barcode data (unique)
    photo_url: Optional[str] = None  # base64 or URL
    photo_status: PhotoStatus = PhotoStatus.PENDING
    submitted_photo_url: Optional[str] = None  # base64 or URL
    photo_reviewed_by: Optional[str] = None  # Reference to User
    photo_reviewed_at: Optional[datetime] = None
    is_active: bool = True
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    deactivated_by: Optional[str] = None  # Reference to User
    deactivation_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class DigitalIDCreate(BaseModel):
    user_id: str
    qr_code: str
    barcode: str
    photo_url: Optional[str] = None
    expires_at: Optional[datetime] = None

class DigitalIDUpdate(BaseModel):
    photo_url: Optional[str] = None
    submitted_photo_url: Optional[str] = None
    photo_status: Optional[PhotoStatus] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

# ID Scan Log Models
class IDScanLog(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    digital_id_id: str  # Reference to DigitalID
    scanned_by: Optional[str] = None  # Reference to User
    location: Optional[str] = None
    purpose: Optional[ScanPurpose] = None
    device_info: Optional[str] = None
    scan_result: str = "success"  # success, failed, etc.
    scanned_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class IDScanLogCreate(BaseModel):
    digital_id_id: str
    scanned_by: Optional[str] = None
    location: Optional[str] = None
    purpose: Optional[ScanPurpose] = None
    device_info: Optional[str] = None
    scan_result: str = "success"

    class Config:
        use_enum_values = True
