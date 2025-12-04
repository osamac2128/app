"""Bell schedule models"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, time
from enum import Enum


class ScheduleType(str, Enum):
    """Types of school schedules"""
    REGULAR = "regular"
    EARLY_RELEASE = "early_release"
    EXAM = "exam"
    ASSEMBLY = "assembly"
    HALF_DAY = "half_day"
    CUSTOM = "custom"


class Period(BaseModel):
    """Individual period in schedule"""
    period_number: int
    period_name: str  # e.g., "Period 1", "Lunch A", "Advisory"
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    is_passing_period: bool = False
    is_lunch: bool = False
    allow_passes: bool = True  # Can students request passes during this time


class BellSchedule(BaseModel):
    """School bell schedule"""
    _id: Optional[str] = Field(alias='_id', default=None)
    name: str
    schedule_type: ScheduleType
    periods: List[Period]
    is_default: bool = False
    is_active: bool = True
    effective_dates: Optional[List[str]] = None  # List of dates this schedule applies
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
        populate_by_name = True


class BellScheduleCreate(BaseModel):
    """Create bell schedule request"""
    name: str
    schedule_type: ScheduleType
    periods: List[Period]
    is_default: bool = False
    effective_dates: Optional[List[str]] = None

    class Config:
        use_enum_values = True


class CurrentPeriodInfo(BaseModel):
    """Information about current period"""
    current_period: Optional[Period] = None
    next_period: Optional[Period] = None
    time_remaining_minutes: Optional[int] = None
    is_between_periods: bool = False
    schedule_name: str
