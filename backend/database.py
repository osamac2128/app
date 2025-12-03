from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.getenv('DB_NAME', 'aisj_connect')

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None

async def connect_to_mongo():
    """Connect to MongoDB and create indexes"""
    global client, db
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        logger.info(f"Connected to MongoDB: {db_name}")
        
        # Create indexes for all collections
        await create_indexes()
        
        # Insert initial seed data
        await seed_initial_data()
        
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        logger.info("Closed MongoDB connection")

async def create_indexes():
    """Create indexes for all collections"""
    logger.info("Creating indexes...")
    
    # Users indexes
    await db.users.create_indexes([
        IndexModel([('email', ASCENDING)], unique=True),
        IndexModel([('role', ASCENDING)]),
        IndexModel([('status', ASCENDING)]),
    ])
    
    # Students indexes
    await db.students.create_indexes([
        IndexModel([('user_id', ASCENDING)]),
        IndexModel([('student_id', ASCENDING)], unique=True),
        IndexModel([('grade', ASCENDING)]),
        IndexModel([('division', ASCENDING)]),
    ])
    
    # Staff indexes
    await db.staff.create_indexes([
        IndexModel([('user_id', ASCENDING)]),
        IndexModel([('employee_id', ASCENDING)], unique=True),
    ])
    
    # Parent-Student Relations indexes
    await db.parent_student_relations.create_indexes([
        IndexModel([('parent_user_id', ASCENDING)]),
        IndexModel([('student_id', ASCENDING)]),
        IndexModel([('parent_user_id', ASCENDING), ('student_id', ASCENDING)], unique=True),
    ])
    
    # Digital IDs indexes
    await db.digital_ids.create_indexes([
        IndexModel([('user_id', ASCENDING)], unique=True),
        IndexModel([('qr_code', ASCENDING)], unique=True),
        IndexModel([('barcode', ASCENDING)], unique=True),
        IndexModel([('is_active', ASCENDING)]),
    ])
    
    # ID Scan Logs indexes
    await db.id_scan_logs.create_indexes([
        IndexModel([('digital_id_id', ASCENDING)]),
        IndexModel([('scanned_at', DESCENDING)]),
    ])
    
    # Locations indexes
    await db.locations.create_indexes([
        IndexModel([('type', ASCENDING)]),
        IndexModel([('building', ASCENDING)]),
        IndexModel([('is_active', ASCENDING)]),
    ])
    
    # Passes indexes
    await db.passes.create_indexes([
        IndexModel([('student_id', ASCENDING)]),
        IndexModel([('status', ASCENDING)]),
        IndexModel([('requested_at', DESCENDING)]),
        IndexModel([('origin_location_id', ASCENDING)]),
        IndexModel([('destination_location_id', ASCENDING)]),
    ])
    
    # Encounter Groups indexes
    await db.encounter_groups.create_indexes([
        IndexModel([('is_active', ASCENDING)]),
    ])
    
    # Emergency Alerts indexes
    await db.emergency_alerts.create_indexes([
        IndexModel([('type', ASCENDING)]),
        IndexModel([('triggered_at', DESCENDING)]),
        IndexModel([('resolved_at', ASCENDING)]),
    ])
    
    # Emergency Check-ins indexes
    await db.emergency_check_ins.create_indexes([
        IndexModel([('alert_id', ASCENDING)]),
        IndexModel([('user_id', ASCENDING)]),
        IndexModel([('status', ASCENDING)]),
        IndexModel([('alert_id', ASCENDING), ('user_id', ASCENDING)], unique=True),
    ])
    
    # Notifications indexes
    await db.notifications.create_indexes([
        IndexModel([('status', ASCENDING)]),
        IndexModel([('scheduled_at', ASCENDING)]),
        IndexModel([('created_at', DESCENDING)]),
    ])
    
    # Notification Receipts indexes
    await db.notification_receipts.create_indexes([
        IndexModel([('notification_id', ASCENDING)]),
        IndexModel([('user_id', ASCENDING)]),
        IndexModel([('delivery_status', ASCENDING)]),
        IndexModel([('notification_id', ASCENDING), ('user_id', ASCENDING)], unique=True),
    ])
    
    # Visitors indexes
    await db.visitors.create_indexes([
        IndexModel([('last_name', ASCENDING), ('first_name', ASCENDING)]),
        IndexModel([('id_number', ASCENDING)]),
        IndexModel([('is_on_watchlist', ASCENDING)]),
    ])
    
    # Visitor Logs indexes
    await db.visitor_logs.create_indexes([
        IndexModel([('visitor_id', ASCENDING)]),
        IndexModel([('checked_in_at', DESCENDING)]),
        IndexModel([('checked_out_at', ASCENDING)]),
        IndexModel([('host_user_id', ASCENDING)]),
    ])
    
    # Visitor Pre-registrations indexes
    await db.visitor_pre_registrations.create_indexes([
        IndexModel([('expected_date', ASCENDING)]),
        IndexModel([('access_code', ASCENDING)], unique=True, sparse=True),
    ])
    
    # Audit Logs indexes
    await db.audit_logs.create_indexes([
        IndexModel([('user_id', ASCENDING)]),
        IndexModel([('action', ASCENDING)]),
        IndexModel([('entity_type', ASCENDING), ('entity_id', ASCENDING)]),
        IndexModel([('created_at', DESCENDING)]),
    ])
    
    # App Settings indexes
    await db.app_settings.create_indexes([
        IndexModel([('key', ASCENDING)], unique=True),
    ])
    
    logger.info("Indexes created successfully")

async def seed_initial_data():
    """Insert initial seed data"""
    logger.info("Seeding initial data...")
    
    # Check if locations already exist
    existing_locations = await db.locations.count_documents({})
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
        await db.locations.insert_many(locations)
        logger.info("Inserted default locations")
    
    # Check if app settings already exist
    existing_settings = await db.app_settings.count_documents({})
    if existing_settings == 0:
        # Insert default app settings
        settings = [
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
        await db.app_settings.insert_many(settings)
        logger.info("Inserted default app settings")
    
    logger.info("Initial data seeding complete")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db
