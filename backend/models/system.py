from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# Audit Log Models
class AuditLog(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: Optional[str] = None  # Reference to User
    action: str  # e.g., "create", "update", "delete", "login", etc.
    entity_type: str  # e.g., "user", "pass", "visitor", etc.
    entity_id: Optional[str] = None  # Reference to the entity
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class AuditLogCreate(BaseModel):
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

# App Settings Models
class AppSetting(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    key: str  # Unique key
    value: Any  # Can be any JSON-compatible value
    description: Optional[str] = None
    updated_by: Optional[str] = None  # Reference to User
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class AppSettingCreate(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None
    updated_by: Optional[str] = None

class AppSettingUpdate(BaseModel):
    value: Optional[Any] = None
    description: Optional[str] = None
    updated_by: Optional[str] = None
