from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.core.database import get_database
from utils.dependencies import get_current_active_user, require_role
from models.notifications import (
    Notification, NotificationCreate, NotificationStatus,
    NotificationReceipt, DeliveryStatus
)
from models.users import UserRole
from bson import ObjectId

router = APIRouter(prefix='/notifications', tags=['Notifications'])


class ScheduledNotificationCreate(BaseModel):
    title: str
    body: str
    type: str = 'announcement'
    target_roles: Optional[List[str]] = None
    scheduled_for: datetime
    priority: str = 'normal'

@router.post('/send', response_model=Notification)
async def send_notification(
    notification_data: NotificationCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Create and send a notification."""
    
    new_notification = notification_data.dict()
    new_notification['created_at'] = datetime.utcnow()
    new_notification['updated_at'] = datetime.utcnow()
    new_notification['status'] = NotificationStatus.SENT
    new_notification['sent_at'] = datetime.utcnow()
    new_notification['created_by'] = str(current_user['_id'])
    
    result = await db.notifications.insert_one(new_notification)
    new_notification['_id'] = str(result.inserted_id)
    
    # In a real app, we would trigger background tasks here to:
    # 1. Create NotificationReceipts for all target users
    # 2. Send actual Push Notifications via FCM/Expo
    
    return new_notification

@router.get('/my-notifications', response_model=List[Notification])
async def get_my_notifications(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Fetch notifications for the current user."""
    user_role = current_user['role']
    user_id = str(current_user['_id'])
    
    # Simple logic: Fetch notifications targeting the user's role or specifically the user
    # In production, this should be optimized with indexes and receipt tracking
    notifications = await db.notifications.find({
        '$or': [
            {'target_roles': user_role},
            {'target_user_ids': user_id},
            {'target_roles': None, 'target_user_ids': None} # Global? Maybe not safe, but for demo ok
        ],
        'status': NotificationStatus.SENT
    }).sort('created_at', -1).to_list(length=50)
    
    for n in notifications:
        n['_id'] = str(n['_id'])
        
    return notifications

@router.get('/sent', response_model=List[Notification])
async def get_sent_notifications(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Fetch notifications sent by the current user."""
    user_id = str(current_user['_id'])
    
    # Fetch all notifications created by this user
    notifications = await db.notifications.find({
        'created_by': user_id,
        'status': NotificationStatus.SENT
    }).sort('created_at', -1).to_list(length=100)
    
    # Convert ObjectId to string and calculate recipient counts
    for n in notifications:
        n['_id'] = str(n['_id'])
        
        # Calculate recipient count based on target_roles
        if n.get('target_roles'):
            # Count users with those roles
            recipient_count = 0
            for role in n['target_roles']:
                count = await db.users.count_documents({'role': role, 'status': 'active'})
                recipient_count += count
            n['recipient_count'] = recipient_count
        elif n.get('target_user_ids'):
            n['recipient_count'] = len(n['target_user_ids'])
        else:
            # All users
            n['recipient_count'] = await db.users.count_documents({'status': 'active'})
    
    return notifications

@router.post('/mark-read/{notification_id}')
async def mark_read(
    notification_id: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Mark a notification as read."""
    user_id = str(current_user['_id'])

    # Check if receipt exists
    receipt = await db.notification_receipts.find_one({
        'notification_id': notification_id,
        'user_id': user_id
    })

    if receipt:
        await db.notification_receipts.update_one(
            {'_id': receipt['_id']},
            {'$set': {'read_at': datetime.utcnow(), 'updated_at': datetime.utcnow()}}
        )
    else:
        # Create receipt
        new_receipt = {
            'notification_id': notification_id,
            'user_id': user_id,
            'delivered_at': datetime.utcnow(), # Assumed delivered if they are reading it
            'read_at': datetime.utcnow(),
            'delivery_status': DeliveryStatus.DELIVERED,
            'created_at': datetime.utcnow()
        }
        await db.notification_receipts.insert_one(new_receipt)

    return {"status": "success"}


@router.post('/schedule')
async def schedule_notification(
    notification_data: ScheduledNotificationCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Schedule a notification for future delivery."""

    # Validate scheduled time is in the future
    if notification_data.scheduled_for <= datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Scheduled time must be in the future"
        )

    new_notification = {
        'title': notification_data.title,
        'body': notification_data.body,
        'type': notification_data.type,
        'target_roles': notification_data.target_roles,
        'priority': notification_data.priority,
        'scheduled_for': notification_data.scheduled_for,
        'status': 'scheduled',
        'created_by': str(current_user['_id']),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }

    result = await db.notifications.insert_one(new_notification)
    new_notification['_id'] = str(result.inserted_id)

    return {
        'message': 'Notification scheduled successfully',
        'notification': new_notification
    }


@router.get('/scheduled')
async def get_scheduled_notifications(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Get all scheduled notifications."""
    user_id = str(current_user['_id'])

    scheduled = await db.notifications.find({
        'status': 'scheduled',
        'scheduled_for': {'$gte': datetime.utcnow()}
    }).sort('scheduled_for', 1).to_list(length=100)

    for n in scheduled:
        n['_id'] = str(n['_id'])

    return scheduled


@router.delete('/scheduled/{notification_id}')
async def cancel_scheduled_notification(
    notification_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Cancel a scheduled notification."""

    notification = await db.notifications.find_one({
        '_id': ObjectId(notification_id),
        'status': 'scheduled'
    })

    if not notification:
        raise HTTPException(status_code=404, detail="Scheduled notification not found")

    await db.notifications.update_one(
        {'_id': ObjectId(notification_id)},
        {'$set': {'status': 'cancelled', 'updated_at': datetime.utcnow()}}
    )

    return {'message': 'Scheduled notification cancelled'}


@router.get('/templates')
async def get_notification_templates(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Admin/Staff) Get notification templates."""

    templates = await db.notification_templates.find({}).to_list(length=100)

    for t in templates:
        t['_id'] = str(t['_id'])

    # If no templates exist, return default templates
    if not templates:
        templates = [
            {
                '_id': 'default_1',
                'name': 'School Closure',
                'title': 'School Closure Notice',
                'body': 'Due to [REASON], school will be closed on [DATE]. Please stay safe and check for updates.',
                'type': 'announcement'
            },
            {
                '_id': 'default_2',
                'name': 'Event Reminder',
                'title': 'Upcoming Event Reminder',
                'body': 'This is a reminder that [EVENT] will take place on [DATE] at [TIME]. Please mark your calendars.',
                'type': 'reminder'
            },
            {
                '_id': 'default_3',
                'name': 'Early Dismissal',
                'title': 'Early Dismissal Notice',
                'body': 'Students will be dismissed early today at [TIME] due to [REASON]. Please arrange for pickup accordingly.',
                'type': 'announcement'
            },
            {
                '_id': 'default_4',
                'name': 'General Announcement',
                'title': 'Important Announcement',
                'body': '[YOUR MESSAGE HERE]',
                'type': 'general'
            },
            {
                '_id': 'default_5',
                'name': 'Parent Meeting',
                'title': 'Parent-Teacher Meeting',
                'body': 'Parent-Teacher meetings are scheduled for [DATE]. Please sign up for your preferred time slot through the school portal.',
                'type': 'reminder'
            }
        ]

    return templates
