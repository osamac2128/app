from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
from app.core.database import get_database
from utils.dependencies import get_current_active_user, require_role
from models.notifications import (
    Notification, NotificationCreate, NotificationStatus,
    NotificationReceipt, DeliveryStatus
)
from models.users import UserRole
from bson import ObjectId

router = APIRouter(prefix='/notifications', tags=['Notifications'])

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
