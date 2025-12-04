from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URL)
            self.db = self.client[settings.DB_NAME]
            logger.info(f"Connected to MongoDB: {settings.DB_NAME}")
            
            # Verify connection
            await self.client.admin.command('ping')
            logger.info("Database connection verified")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

db = Database()

async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database instance"""
    return db.db
