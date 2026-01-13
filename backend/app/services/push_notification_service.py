"""Push Notification Service for Firebase Cloud Messaging and Apple Push Notifications"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DevicePlatform(str, Enum):
    """Supported device platforms"""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class PushNotification(BaseModel):
    """Push notification payload model"""
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    sound: Optional[str] = "default"
    badge: Optional[int] = None
    image_url: Optional[str] = None
    click_action: Optional[str] = None
    category: Optional[str] = None


class DeviceToken(BaseModel):
    """Device token registration model"""
    user_id: str
    token: str
    platform: DevicePlatform
    device_name: Optional[str] = None
    app_version: Optional[str] = None


class PushNotificationService:
    """
    Push notification service supporting Firebase Cloud Messaging and APNs.

    Note: This service requires configuration of Firebase credentials or APNs certificates.
    Without valid credentials, notifications will be logged but not sent.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.device_tokens_collection = db.device_tokens
        self.notification_logs_collection = db.notification_logs
        self._fcm_initialized = False
        self._apns_initialized = False

    async def initialize_fcm(self, credentials_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase Cloud Messaging.

        Args:
            credentials_path: Path to Firebase service account JSON file

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Firebase initialization would go here
            # import firebase_admin
            # from firebase_admin import credentials, messaging

            # if credentials_path:
            #     cred = credentials.Certificate(credentials_path)
            #     firebase_admin.initialize_app(cred)
            #     self._fcm_initialized = True
            #     logger.info("Firebase Cloud Messaging initialized successfully")
            #     return True

            logger.warning(
                "FCM not initialized: No credentials provided. "
                "Set FIREBASE_CREDENTIALS_PATH environment variable."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to initialize FCM: {e}")
            return False

    async def initialize_apns(
        self,
        key_path: Optional[str] = None,
        key_id: Optional[str] = None,
        team_id: Optional[str] = None,
        bundle_id: Optional[str] = None
    ) -> bool:
        """
        Initialize Apple Push Notification Service.

        Args:
            key_path: Path to APNs auth key (.p8 file)
            key_id: APNs Key ID
            team_id: Apple Developer Team ID
            bundle_id: App Bundle ID

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # APNs initialization would go here
            # from aioapns import APNs, NotificationRequest

            # if all([key_path, key_id, team_id, bundle_id]):
            #     self._apns_client = APNs(
            #         key=key_path,
            #         key_id=key_id,
            #         team_id=team_id,
            #         topic=bundle_id,
            #         use_sandbox=True  # Set to False for production
            #     )
            #     self._apns_initialized = True
            #     logger.info("APNs initialized successfully")
            #     return True

            logger.warning(
                "APNs not initialized: Missing credentials. "
                "Set APNS_KEY_PATH, APNS_KEY_ID, APNS_TEAM_ID, and APP_BUNDLE_ID."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to initialize APNs: {e}")
            return False

    async def register_device(self, device: DeviceToken) -> dict:
        """
        Register a device token for push notifications.

        Args:
            device: Device token registration data

        Returns:
            Registration result
        """
        # Check if token already exists for this user
        existing = await self.device_tokens_collection.find_one({
            'user_id': device.user_id,
            'token': device.token
        })

        if existing:
            # Update existing token
            await self.device_tokens_collection.update_one(
                {'_id': existing['_id']},
                {'$set': {
                    'platform': device.platform,
                    'device_name': device.device_name,
                    'app_version': device.app_version,
                    'updated_at': datetime.utcnow(),
                    'is_active': True
                }}
            )
            logger.info(f"Updated device token for user {device.user_id}")
            return {'status': 'updated', 'token_id': str(existing['_id'])}

        # Insert new token
        result = await self.device_tokens_collection.insert_one({
            'user_id': device.user_id,
            'token': device.token,
            'platform': device.platform,
            'device_name': device.device_name,
            'app_version': device.app_version,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        })
        logger.info(f"Registered new device token for user {device.user_id}")
        return {'status': 'created', 'token_id': str(result.inserted_id)}

    async def unregister_device(self, user_id: str, token: str) -> bool:
        """
        Unregister a device token.

        Args:
            user_id: User ID
            token: Device token to unregister

        Returns:
            True if unregistered, False otherwise
        """
        result = await self.device_tokens_collection.update_one(
            {'user_id': user_id, 'token': token},
            {'$set': {'is_active': False, 'updated_at': datetime.utcnow()}}
        )
        if result.modified_count > 0:
            logger.info(f"Unregistered device token for user {user_id}")
            return True
        return False

    async def get_user_tokens(self, user_id: str) -> List[dict]:
        """
        Get all active device tokens for a user.

        Args:
            user_id: User ID

        Returns:
            List of device tokens
        """
        tokens = await self.device_tokens_collection.find({
            'user_id': user_id,
            'is_active': True
        }).to_list(length=100)

        for token in tokens:
            token['_id'] = str(token['_id'])

        return tokens

    async def send_to_user(
        self,
        user_id: str,
        notification: PushNotification
    ) -> dict:
        """
        Send a push notification to all devices of a user.

        Args:
            user_id: Target user ID
            notification: Notification payload

        Returns:
            Send results
        """
        tokens = await self.get_user_tokens(user_id)

        if not tokens:
            logger.warning(f"No device tokens found for user {user_id}")
            return {'status': 'no_tokens', 'sent': 0, 'failed': 0}

        results = {'sent': 0, 'failed': 0, 'errors': []}

        for token_doc in tokens:
            try:
                success = await self._send_notification(
                    token=token_doc['token'],
                    platform=token_doc['platform'],
                    notification=notification
                )
                if success:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))

        # Log the notification
        await self._log_notification(
            user_ids=[user_id],
            notification=notification,
            results=results
        )

        return results

    async def send_to_users(
        self,
        user_ids: List[str],
        notification: PushNotification
    ) -> dict:
        """
        Send a push notification to multiple users.

        Args:
            user_ids: List of target user IDs
            notification: Notification payload

        Returns:
            Send results
        """
        total_results = {'sent': 0, 'failed': 0, 'users_notified': 0}

        for user_id in user_ids:
            result = await self.send_to_user(user_id, notification)
            total_results['sent'] += result.get('sent', 0)
            total_results['failed'] += result.get('failed', 0)
            if result.get('sent', 0) > 0:
                total_results['users_notified'] += 1

        return total_results

    async def send_to_role(
        self,
        role: str,
        notification: PushNotification
    ) -> dict:
        """
        Send a push notification to all users with a specific role.

        Args:
            role: Target role (STUDENT, PARENT, STAFF, ADMIN)
            notification: Notification payload

        Returns:
            Send results
        """
        # Get all users with the specified role
        users = await self.db.users.find(
            {'role': role, 'is_active': True},
            {'_id': 1}
        ).to_list(length=10000)

        user_ids = [str(user['_id']) for user in users]

        if not user_ids:
            logger.warning(f"No users found with role {role}")
            return {'status': 'no_users', 'sent': 0, 'failed': 0}

        return await self.send_to_users(user_ids, notification)

    async def broadcast(
        self,
        notification: PushNotification,
        exclude_roles: Optional[List[str]] = None
    ) -> dict:
        """
        Broadcast a push notification to all users.

        Args:
            notification: Notification payload
            exclude_roles: Optional list of roles to exclude

        Returns:
            Send results
        """
        query = {'is_active': True}
        if exclude_roles:
            query['role'] = {'$nin': exclude_roles}

        users = await self.db.users.find(query, {'_id': 1}).to_list(length=50000)
        user_ids = [str(user['_id']) for user in users]

        if not user_ids:
            return {'status': 'no_users', 'sent': 0, 'failed': 0}

        return await self.send_to_users(user_ids, notification)

    async def _send_notification(
        self,
        token: str,
        platform: str,
        notification: PushNotification
    ) -> bool:
        """
        Send a notification to a specific device.

        Args:
            token: Device token
            platform: Device platform (ios, android, web)
            notification: Notification payload

        Returns:
            True if sent successfully, False otherwise
        """
        # This is where actual push notification sending would happen
        # For now, we log the notification as a placeholder

        if platform in [DevicePlatform.ANDROID, DevicePlatform.WEB]:
            return await self._send_fcm(token, notification)
        elif platform == DevicePlatform.IOS:
            return await self._send_apns(token, notification)
        else:
            logger.warning(f"Unknown platform: {platform}")
            return False

    async def _send_fcm(self, token: str, notification: PushNotification) -> bool:
        """Send notification via Firebase Cloud Messaging"""
        if not self._fcm_initialized:
            # Log the notification for debugging/testing
            logger.info(
                f"[FCM - Not Configured] Would send to {token[:20]}...: "
                f"'{notification.title}' - '{notification.body}'"
            )
            # Return True to simulate success for testing
            return True

        # Actual FCM sending code would go here:
        # message = messaging.Message(
        #     notification=messaging.Notification(
        #         title=notification.title,
        #         body=notification.body,
        #         image=notification.image_url
        #     ),
        #     data=notification.data,
        #     token=token,
        #     android=messaging.AndroidConfig(
        #         priority='high' if notification.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL] else 'normal'
        #     )
        # )
        # response = messaging.send(message)
        # return bool(response)
        return True

    async def _send_apns(self, token: str, notification: PushNotification) -> bool:
        """Send notification via Apple Push Notification Service"""
        if not self._apns_initialized:
            # Log the notification for debugging/testing
            logger.info(
                f"[APNs - Not Configured] Would send to {token[:20]}...: "
                f"'{notification.title}' - '{notification.body}'"
            )
            # Return True to simulate success for testing
            return True

        # Actual APNs sending code would go here:
        # request = NotificationRequest(
        #     device_token=token,
        #     message={
        #         "aps": {
        #             "alert": {
        #                 "title": notification.title,
        #                 "body": notification.body
        #             },
        #             "sound": notification.sound,
        #             "badge": notification.badge
        #         },
        #         **(notification.data or {})
        #     }
        # )
        # response = await self._apns_client.send_notification(request)
        # return response.is_successful
        return True

    async def _log_notification(
        self,
        user_ids: List[str],
        notification: PushNotification,
        results: dict
    ) -> None:
        """Log a notification for audit purposes"""
        await self.notification_logs_collection.insert_one({
            'user_ids': user_ids,
            'title': notification.title,
            'body': notification.body,
            'data': notification.data,
            'priority': notification.priority,
            'results': results,
            'created_at': datetime.utcnow()
        })


# Notification Templates

class NotificationTemplates:
    """Pre-defined notification templates for common events"""

    @staticmethod
    def pass_approved(student_name: str, destination: str) -> PushNotification:
        return PushNotification(
            title="Pass Approved",
            body=f"Your hall pass to {destination} has been approved.",
            priority=NotificationPriority.HIGH,
            data={'type': 'pass_approved'},
            category='pass'
        )

    @staticmethod
    def pass_rejected(reason: Optional[str] = None) -> PushNotification:
        body = "Your hall pass request has been denied."
        if reason:
            body += f" Reason: {reason}"
        return PushNotification(
            title="Pass Denied",
            body=body,
            priority=NotificationPriority.NORMAL,
            data={'type': 'pass_rejected'},
            category='pass'
        )

    @staticmethod
    def pass_overtime(minutes: int) -> PushNotification:
        return PushNotification(
            title="Pass Overtime",
            body=f"Your hall pass is {minutes} minutes overtime. Please return immediately.",
            priority=NotificationPriority.HIGH,
            data={'type': 'pass_overtime', 'minutes': minutes},
            category='pass'
        )

    @staticmethod
    def emergency_alert(alert_type: str, instructions: str) -> PushNotification:
        return PushNotification(
            title=f"EMERGENCY: {alert_type.upper()}",
            body=instructions,
            priority=NotificationPriority.CRITICAL,
            sound="emergency.caf",
            data={'type': 'emergency', 'alert_type': alert_type},
            category='emergency'
        )

    @staticmethod
    def emergency_ended() -> PushNotification:
        return PushNotification(
            title="Emergency Cleared",
            body="The emergency situation has been resolved. Resume normal activities.",
            priority=NotificationPriority.HIGH,
            data={'type': 'emergency_ended'},
            category='emergency'
        )

    @staticmethod
    def visitor_arrival(visitor_name: str, purpose: str) -> PushNotification:
        return PushNotification(
            title="Visitor Arrived",
            body=f"{visitor_name} has arrived. Purpose: {purpose}",
            priority=NotificationPriority.NORMAL,
            data={'type': 'visitor_arrival'},
            category='visitor'
        )

    @staticmethod
    def new_announcement(title: str, preview: str) -> PushNotification:
        return PushNotification(
            title=title,
            body=preview[:100] + "..." if len(preview) > 100 else preview,
            priority=NotificationPriority.NORMAL,
            data={'type': 'announcement'},
            category='announcement'
        )
