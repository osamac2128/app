from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING
from app.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    """Database connection manager for MongoDB"""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Connect to MongoDB and initialize database"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URL)
            self.db = self.client[settings.DB_NAME]
            logger.info(f"Connected to MongoDB: {settings.DB_NAME}")

            # Verify connection
            await self.client.admin.command('ping')
            logger.info("Database connection verified")

            # Create indexes for all collections
            await self._create_indexes()

            # Insert initial seed data
            await self._seed_initial_data()

            logger.info("Database initialization complete")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

    async def _create_indexes(self) -> None:
        """Create indexes for all collections"""
        logger.info("Creating indexes...")

        # Users indexes
        await self.db.users.create_indexes([
            IndexModel([('email', ASCENDING)], unique=True),
            IndexModel([('role', ASCENDING)]),
            IndexModel([('status', ASCENDING)]),
        ])

        # Students indexes
        await self.db.students.create_indexes([
            IndexModel([('user_id', ASCENDING)]),
            IndexModel([('student_id', ASCENDING)], unique=True),
            IndexModel([('grade', ASCENDING)]),
            IndexModel([('division', ASCENDING)]),
        ])

        # Staff indexes
        await self.db.staff.create_indexes([
            IndexModel([('user_id', ASCENDING)]),
            IndexModel([('employee_id', ASCENDING)], unique=True),
        ])

        # Parent-Student Relations indexes
        await self.db.parent_student_relations.create_indexes([
            IndexModel([('parent_user_id', ASCENDING)]),
            IndexModel([('student_id', ASCENDING)]),
            IndexModel([('parent_user_id', ASCENDING), ('student_id', ASCENDING)], unique=True),
        ])

        # Digital IDs indexes
        await self.db.digital_ids.create_indexes([
            IndexModel([('user_id', ASCENDING)], unique=True),
            IndexModel([('qr_code', ASCENDING)], unique=True),
            IndexModel([('barcode', ASCENDING)], unique=True),
            IndexModel([('is_active', ASCENDING)]),
        ])

        # ID Scan Logs indexes
        await self.db.id_scan_logs.create_indexes([
            IndexModel([('digital_id_id', ASCENDING)]),
            IndexModel([('scanned_at', DESCENDING)]),
        ])

        # Locations indexes
        await self.db.locations.create_indexes([
            IndexModel([('type', ASCENDING)]),
            IndexModel([('building', ASCENDING)]),
            IndexModel([('is_active', ASCENDING)]),
        ])

        # Passes indexes
        await self.db.passes.create_indexes([
            IndexModel([('student_id', ASCENDING)]),
            IndexModel([('status', ASCENDING)]),
            IndexModel([('requested_at', DESCENDING)]),
            IndexModel([('origin_location_id', ASCENDING)]),
            IndexModel([('destination_location_id', ASCENDING)]),
        ])

        # Encounter Groups indexes
        await self.db.encounter_groups.create_indexes([
            IndexModel([('is_active', ASCENDING)]),
        ])

        # Emergency Alerts indexes
        await self.db.emergency_alerts.create_indexes([
            IndexModel([('type', ASCENDING)]),
            IndexModel([('triggered_at', DESCENDING)]),
            IndexModel([('resolved_at', ASCENDING)]),
        ])

        # Emergency Check-ins indexes
        await self.db.emergency_check_ins.create_indexes([
            IndexModel([('alert_id', ASCENDING)]),
            IndexModel([('user_id', ASCENDING)]),
            IndexModel([('status', ASCENDING)]),
            IndexModel([('alert_id', ASCENDING), ('user_id', ASCENDING)], unique=True),
        ])

        # Notifications indexes
        await self.db.notifications.create_indexes([
            IndexModel([('status', ASCENDING)]),
            IndexModel([('scheduled_at', ASCENDING)]),
            IndexModel([('created_at', DESCENDING)]),
        ])

        # Notification Receipts indexes
        await self.db.notification_receipts.create_indexes([
            IndexModel([('notification_id', ASCENDING)]),
            IndexModel([('user_id', ASCENDING)]),
            IndexModel([('delivery_status', ASCENDING)]),
            IndexModel([('notification_id', ASCENDING), ('user_id', ASCENDING)], unique=True),
        ])

        # Visitors indexes
        await self.db.visitors.create_indexes([
            IndexModel([('last_name', ASCENDING), ('first_name', ASCENDING)]),
            IndexModel([('id_number', ASCENDING)]),
            IndexModel([('is_on_watchlist', ASCENDING)]),
        ])

        # Visitor Logs indexes
        await self.db.visitor_logs.create_indexes([
            IndexModel([('visitor_id', ASCENDING)]),
            IndexModel([('checked_in_at', DESCENDING)]),
            IndexModel([('checked_out_at', ASCENDING)]),
            IndexModel([('host_user_id', ASCENDING)]),
        ])

        # Visitor Pre-registrations indexes
        await self.db.visitor_pre_registrations.create_indexes([
            IndexModel([('expected_date', ASCENDING)]),
            IndexModel([('access_code', ASCENDING)], unique=True, sparse=True),
        ])

        # Audit Logs indexes
        await self.db.audit_logs.create_indexes([
            IndexModel([('user_id', ASCENDING)]),
            IndexModel([('action', ASCENDING)]),
            IndexModel([('entity_type', ASCENDING), ('entity_id', ASCENDING)]),
            IndexModel([('created_at', DESCENDING)]),
        ])

        # App Settings indexes
        await self.db.app_settings.create_indexes([
            IndexModel([('key', ASCENDING)], unique=True),
        ])

        logger.info("Indexes created successfully")

    async def _seed_initial_data(self) -> None:
        """Insert initial seed data"""
        logger.info("Seeding initial data...")

        # Check if locations already exist
        existing_locations = await self.db.locations.count_documents({})
        if existing_locations == 0:
            # Insert common location types
            locations = [
                {
                    "name": "Main Office",
                    "type": "office",
                    "max_capacity": None,
                    "requires_approval": True,
                    "default_time_limit_minutes": 5,
                    "is_active": True
                },
                {
                    "name": "Library",
                    "type": "library",
                    "max_capacity": None,
                    "requires_approval": False,
                    "default_time_limit_minutes": 5,
                    "is_active": True
                },
                {
                    "name": "Gymnasium",
                    "type": "gym",
                    "max_capacity": None,
                    "requires_approval": False,
                    "default_time_limit_minutes": 5,
                    "is_active": True
                },
                {
                    "name": "Cafeteria",
                    "type": "cafeteria",
                    "max_capacity": None,
                    "requires_approval": False,
                    "default_time_limit_minutes": 5,
                    "is_active": True
                },
                {
                    "name": "Nurse's Office",
                    "type": "nurse",
                    "max_capacity": 2,
                    "requires_approval": False,
                    "default_time_limit_minutes": 5,
                    "is_active": True
                },
                {
                    "name": "Counselor's Office",
                    "type": "counselor",
                    "max_capacity": None,
                    "requires_approval": True,
                    "default_time_limit_minutes": 5,
                    "is_active": True
                },
            ]
            await self.db.locations.insert_many(locations)
            logger.info("Inserted default locations")

        # Check if app settings already exist
        existing_settings = await self.db.app_settings.count_documents({})
        if existing_settings == 0:
            # Insert default app settings
            settings_data = [
                {
                    "key": "default_pass_time_limit",
                    "value": 5,
                    "description": "Default pass duration in minutes"
                },
                {
                    "key": "max_daily_passes",
                    "value": 5,
                    "description": "Maximum passes per student per day"
                },
                {
                    "key": "enable_encounter_prevention",
                    "value": True,
                    "description": "Enable encounter prevention feature"
                },
                {
                    "key": "emergency_sms_enabled",
                    "value": True,
                    "description": "Send SMS for emergency alerts"
                },
                {
                    "key": "visitor_badge_required",
                    "value": True,
                    "description": "Require visitor badges"
                },
            ]
            await self.db.app_settings.insert_many(settings_data)
            logger.info("Inserted default app settings")

        logger.info("Initial data seeding complete")

# Global database instance
db = Database()

async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database instance"""
    return db.db
