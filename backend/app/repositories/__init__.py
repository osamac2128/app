"""Repository package for database operations"""

from app.repositories.base_repository import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.pass_repository import PassRepository, LocationRepository
from app.repositories.digital_id_repository import DigitalIDRepository, IDScanLogRepository
from app.repositories.emergency_repository import EmergencyAlertRepository, EmergencyCheckInRepository
from app.repositories.notification_repository import (
    NotificationRepository,
    NotificationReceiptRepository,
    NotificationTemplateRepository
)
from app.repositories.visitor_repository import (
    VisitorRepository,
    VisitorLogRepository,
    VisitorPreRegistrationRepository
)

__all__ = [
    "BaseRepository",
    "UserRepository",
    "PassRepository",
    "LocationRepository",
    "DigitalIDRepository",
    "IDScanLogRepository",
    "EmergencyAlertRepository",
    "EmergencyCheckInRepository",
    "NotificationRepository",
    "NotificationReceiptRepository",
    "NotificationTemplateRepository",
    "VisitorRepository",
    "VisitorLogRepository",
    "VisitorPreRegistrationRepository",
]
