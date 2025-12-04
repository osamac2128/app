from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, APIRouter, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

# Import core modules
from app.core.config import settings
from app.core.database import db
from app.core.exceptions import AppException

# Import routes
from routes import auth, digital_ids, passes, emergency, notifications, visitors, admin, user_management

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info(f"Starting up {settings.PROJECT_NAME}...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    try:
        await db.connect()
        logger.info("API startup complete")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down API...")
    await db.close()
    logger.info("API shutdown complete")


# Create the main app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Create a router with the API prefix
api_router = APIRouter(prefix=settings.API_PREFIX)


# Health check routes
@api_router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": settings.PROJECT_NAME,
        "status": "operational",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db.db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Include all route modules
api_router.include_router(auth.router)
api_router.include_router(digital_ids.router)
api_router.include_router(passes.router)
api_router.include_router(emergency.router)
api_router.include_router(notifications.router)
api_router.include_router(visitors.router)
api_router.include_router(admin.router)

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for custom exceptions
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    logger.error(f"Application error: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
