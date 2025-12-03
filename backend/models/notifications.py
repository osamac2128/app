from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .users import UserRole, DivisionType

# Enums
class NotificationType(str, Enum):
    GENERAL = "general"
    ANNOUNCEMENT = "announcement"
    REMINDER = "reminder"
    EVENT = "event"
    URGENT = "urgent"

class NotificationStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    CANCELLED = "cancelled"

class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"

# Notification Models
class Notification(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    title: str
    body: str
    type: NotificationType = NotificationType.GENERAL
    image_url: Optional[str] = None  # base64 or URL
    action_url: Optional[str] = None
    target_roles: Optional[List[UserRole]] = None
    target_grades: Optional[List[str]] = None
    target_divisions: Optional[List[DivisionType]] = None
    target_user_ids: Optional[List[str]] = None
    created_by: str  # Reference to User
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: NotificationStatus = NotificationStatus.DRAFT
    total_recipients: int = 0
    delivered_count: int = 0
    read_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class NotificationCreate(BaseModel):
    title: str
    body: str
    type: NotificationType = NotificationType.GENERAL
    image_url: Optional[str] = None
    action_url: Optional[str] = None
    target_roles: Optional[List[UserRole]] = None
    target_grades: Optional[List[str]] = None
    target_divisions: Optional[List[DivisionType]] = None
    target_user_ids: Optional[List[str]] = None
    created_by: str
    scheduled_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    type: Optional[NotificationType] = None
    image_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[NotificationStatus] = None

    class Config:
        use_enum_values = True

# Notification Receipt Models (delivery tracking)
class NotificationReceipt(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    notification_id: str  # Reference to Notification
    user_id: str  # Reference to User
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class NotificationReceiptCreate(BaseModel):
    notification_id: str
    user_id: str

class NotificationReceiptUpdate(BaseModel):
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_status: Optional[DeliveryStatus] = None
    error_message: Optional[str] = None

    class Config:
        use_enum_values = True

# Notification Template Models
class NotificationTemplate(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    title_template: str
    body_template: str
    type: NotificationType
    created_by: Optional[str] = None  # Reference to User
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        populate_by_name = True

class NotificationTemplateCreate(BaseModel):
    name: str
    title_template: str
    body_template: str
    type: NotificationType
    created_by: Optional[str] = None

    class Config:
        use_enum_values = True

class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    title_template: Optional[str] = None
    body_template: Optional[str] = None
    is_active: Optional[bool] = None
