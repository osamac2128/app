from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

# Import database connection
from database import connect_to_mongo, close_mongo_connection, get_database

# Import routes
from routes import auth

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app without a prefix
app = FastAPI(title="AISJ Connect API", version="1.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Basic health check route
@api_router.get("/")
async def root():
    return {
        "message": "AISJ Connect API",
        "status": "operational",
        "version": "1.0"
    }

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    db = get_database()
    try:
        # Test database connection
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# Include authentication routes
api_router.include_router(auth.router)
from routes import digital_ids
api_router.include_router(digital_ids.router)
from routes import passes
api_router.include_router(passes.router)
from routes import emergency
api_router.include_router(emergency.router)
from routes import notifications
api_router.include_router(notifications.router)
from routes import visitors
api_router.include_router(visitors.router)

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup event
@app.on_event("startup")
async def startup_db_client():
    """Connect to MongoDB on startup"""
    logger.info("Starting up AISJ Connect API...")
    await connect_to_mongo()
    logger.info("API startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown"""
    logger.info("Shutting down API...")
    await close_mongo_connection()
    logger.info("API shutdown complete")
