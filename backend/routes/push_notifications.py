"""Push notification API routes"""

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_database
from app.services.push_notification_service import (
    PushNotificationService,
    DeviceToken,
    DevicePlatform,
    PushNotification,
    NotificationPriority
)
from utils.dependencies import get_current_active_user, require_role
from models.users import UserRole
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix='/push', tags=['Push Notifications'])


# Request Models
class RegisterDeviceRequest(BaseModel):
    """Request to register a device token"""
    token: str
    platform: DevicePlatform
    device_name: Optional[str] = None
    app_version: Optional[str] = None


class UnregisterDeviceRequest(BaseModel):
    """Request to unregister a device token"""
    token: str


class SendNotificationRequest(BaseModel):
    """Request to send a notification"""
    title: str
    body: str
    user_ids: Optional[List[str]] = None
    role: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[dict] = None


# Dependency to get push notification service
async def get_push_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> PushNotificationService:
    """Get push notification service instance"""
    return PushNotificationService(db)


# Routes

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register_device(
    request: RegisterDeviceRequest,
    current_user: dict = Depends(get_current_active_user),
    push_service: PushNotificationService = Depends(get_push_service)
):
    """
    Register a device for push notifications.

    Registers the device token to receive push notifications for the current user.
    """
    device = DeviceToken(
        user_id=str(current_user['_id']),
        token=request.token,
        platform=request.platform,
        device_name=request.device_name,
        app_version=request.app_version
    )
    result = await push_service.register_device(device)
    return result


@router.post('/unregister')
async def unregister_device(
    request: UnregisterDeviceRequest,
    current_user: dict = Depends(get_current_active_user),
    push_service: PushNotificationService = Depends(get_push_service)
):
    """
    Unregister a device from push notifications.

    Removes the device token so it will no longer receive push notifications.
    """
    success = await push_service.unregister_device(
        user_id=str(current_user['_id']),
        token=request.token
    )
    if success:
        return {'status': 'unregistered'}
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Device token not found"
    )


@router.get('/devices')
async def get_registered_devices(
    current_user: dict = Depends(get_current_active_user),
    push_service: PushNotificationService = Depends(get_push_service)
):
    """
    Get all registered devices for the current user.

    Returns a list of all devices registered to receive push notifications.
    """
    tokens = await push_service.get_user_tokens(str(current_user['_id']))
    return {'devices': tokens}


@router.post('/send', dependencies=[Depends(require_role(UserRole.ADMIN))])
async def send_notification(
    request: SendNotificationRequest,
    push_service: PushNotificationService = Depends(get_push_service)
):
    """
    Send a push notification (Admin only).

    Send a notification to specific users, a role, or broadcast to all.
    """
    notification = PushNotification(
        title=request.title,
        body=request.body,
        priority=request.priority,
        data=request.data
    )

    if request.user_ids:
        # Send to specific users
        result = await push_service.send_to_users(request.user_ids, notification)
    elif request.role:
        # Send to all users with a role
        result = await push_service.send_to_role(request.role, notification)
    else:
        # Broadcast to all
        result = await push_service.broadcast(notification)

    return result


@router.post('/send/role/{role}', dependencies=[Depends(require_role(UserRole.ADMIN))])
async def send_to_role(
    role: str,
    request: SendNotificationRequest,
    push_service: PushNotificationService = Depends(get_push_service)
):
    """
    Send a push notification to all users with a specific role (Admin only).
    """
    notification = PushNotification(
        title=request.title,
        body=request.body,
        priority=request.priority,
        data=request.data
    )
    result = await push_service.send_to_role(role, notification)
    return result


@router.post('/broadcast', dependencies=[Depends(require_role(UserRole.ADMIN))])
async def broadcast_notification(
    request: SendNotificationRequest,
    push_service: PushNotificationService = Depends(get_push_service)
):
    """
    Broadcast a push notification to all users (Admin only).
    """
    notification = PushNotification(
        title=request.title,
        body=request.body,
        priority=request.priority,
        data=request.data
    )
    result = await push_service.broadcast(notification)
    return result


@router.get('/status')
async def get_push_status(
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    push_service: PushNotificationService = Depends(get_push_service)
):
    """
    Get push notification service status (Admin only).

    Returns the current status of FCM and APNs integrations.
    """
    return {
        'fcm_initialized': push_service._fcm_initialized,
        'apns_initialized': push_service._apns_initialized,
        'note': 'Push notifications require Firebase/APNs credentials to be configured.'
    }
