# AISJ Connect - Code Refactoring Plan

## Executive Summary

This document outlines a comprehensive refactoring plan for the AISJ Connect codebase to improve code quality, maintainability, consistency, and scalability. The refactoring addresses architectural inconsistencies, code duplication, and prepares the codebase for production deployment.

---

## Current State Analysis

### Issues Identified

#### 1. **Backend Architecture Inconsistencies**
- **Duplicate Database Implementations**: Two separate database connection implementations exist:
  - `/backend/database.py` (legacy, currently in use)
  - `/backend/app/core/database.py` (newer, not in use)
- **Mixed Import Patterns**: Routes import from both `database` (root) and `app.core.*` (app folder)
- **Inconsistent Configuration Management**:
  - `/backend/utils/auth.py` uses direct `os.getenv()` calls
  - `/backend/app/core/config.py` uses Pydantic Settings (better approach)

#### 2. **Code Organization Issues**
- **Flat Route Structure**: All routes in `/backend/routes/` without clear module organization
- **Missing Service Layer**: Business logic mixed directly in route handlers
- **No Repository Pattern**: Database queries scattered across routes
- **Incomplete App Structure**: `/backend/app/` folder exists but is underutilized

#### 3. **Code Quality Issues**
- **Inconsistent Error Handling**: Different error handling patterns across routes
- **Missing Input Validation**: Some endpoints lack comprehensive input validation
- **Hardcoded Values**: Magic numbers and strings throughout the code
- **Weak Type Safety**: Missing type hints in several functions
- **Deprecated Patterns**: Using `@app.on_event` (deprecated in FastAPI 0.109+)

#### 4. **Security Concerns**
- **CORS Configuration**: `allow_origins=["*"]` is overly permissive for production
- **Weak Secret Key**: Default secret key in config is insecure
- **Missing Environment Validation**: No validation that required environment variables are set
- **No Rate Limiting**: Authentication endpoints lack rate limiting
- **Token Expiration**: Inconsistent token expiration times (30 min in config, 1440 in auth.py)

#### 5. **Testing Gaps**
- **Minimal Test Coverage**: Only one test file with basic tests
- **No Unit Tests**: Tests are only integration tests
- **Missing Test Fixtures**: No reusable test data or fixtures
- **No Mock Data**: Tests use real database connections

#### 6. **Documentation Issues**
- **Missing Docstrings**: Many functions lack proper documentation
- **No API Documentation**: No OpenAPI customization or enhanced docs
- **Missing Type Hints**: Several functions lack return type annotations

---

## Refactoring Strategy

### Phase 1: Backend Foundation (Priority: High)

#### 1.1 Consolidate Database Layer
**Goal**: Single, consistent database connection pattern

**Tasks**:
- [ ] Migrate to `/backend/app/core/database.py` as the single source
- [ ] Remove `/backend/database.py` (legacy)
- [ ] Update all imports across routes to use `app.core.database`
- [ ] Implement connection pooling configuration
- [ ] Add database health check improvements
- [ ] Create database dependency injection pattern

**Files Affected**:
- `backend/database.py` (DELETE)
- `backend/app/core/database.py` (ENHANCE)
- `backend/server.py` (UPDATE imports)
- All routes in `backend/routes/*.py` (UPDATE imports)

**Benefits**:
- Single source of truth for database connections
- Better configuration management
- Easier to test and mock

---

#### 1.2 Centralize Configuration
**Goal**: All configuration in one place using Pydantic Settings

**Tasks**:
- [ ] Enhance `/backend/app/core/config.py` with all settings
- [ ] Add environment-specific configs (dev, staging, prod)
- [ ] Remove hardcoded secrets and config values
- [ ] Add configuration validation
- [ ] Create `.env.example` file
- [ ] Update `/backend/utils/auth.py` to use centralized config
- [ ] Add CORS origins to environment configuration

**New Settings**:
```python
class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "AISJ Connect API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    MONGO_URL: str
    DB_NAME: str = "aisj_connect"

    # Security
    SECRET_KEY: str  # REQUIRED, no default
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:19006"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if v == 'your-secret-key-here' or len(v) < 32:
            raise ValueError('SECRET_KEY must be set and at least 32 characters')
        return v
```

**Files Affected**:
- `backend/app/core/config.py` (ENHANCE)
- `backend/utils/auth.py` (UPDATE)
- `backend/server.py` (UPDATE)
- `.env.example` (CREATE)

---

#### 1.3 Implement Service Layer Pattern
**Goal**: Separate business logic from route handlers

**Structure**:
```
backend/
  app/
    services/
      auth_service.py
      digital_id_service.py
      pass_service.py
      emergency_service.py
      notification_service.py
      visitor_service.py
```

**Tasks**:
- [ ] Create service layer directory structure
- [ ] Extract business logic from routes to services
- [ ] Implement dependency injection for services
- [ ] Add comprehensive error handling in services
- [ ] Document all service methods

**Example Pattern**:
```python
# backend/app/services/auth_service.py
class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def register_user(self, user_data: RegisterRequest) -> User:
        """Register a new user with validation and business logic."""
        # Business logic here
        pass

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user credentials."""
        pass
```

**Benefits**:
- Testable business logic
- Reusable across different interfaces
- Cleaner route handlers
- Single responsibility principle

---

#### 1.4 Implement Repository Pattern
**Goal**: Abstract database operations

**Structure**:
```
backend/
  app/
    repositories/
      base_repository.py
      user_repository.py
      pass_repository.py
      digital_id_repository.py
      emergency_repository.py
      notification_repository.py
      visitor_repository.py
```

**Tasks**:
- [ ] Create base repository with common CRUD operations
- [ ] Implement specific repositories for each entity
- [ ] Add query builders for complex queries
- [ ] Implement proper error handling
- [ ] Add logging for database operations

**Example Pattern**:
```python
# backend/app/repositories/base_repository.py
class BaseRepository:
    def __init__(self, db: AsyncIOMotorDatabase, collection_name: str):
        self.db = db
        self.collection = db[collection_name]

    async def find_by_id(self, id: str) -> Optional[dict]:
        return await self.collection.find_one({"_id": ObjectId(id)})

    async def find_one(self, query: dict) -> Optional[dict]:
        return await self.collection.find_one(query)

    async def find_many(self, query: dict, limit: int = 100) -> List[dict]:
        return await self.collection.find(query).to_list(length=limit)

    async def insert_one(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def update_one(self, id: str, data: dict) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0

    async def delete_one(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
```

**Benefits**:
- Centralized database logic
- Easier to switch databases if needed
- Consistent query patterns
- Better testability

---

#### 1.5 Improve Error Handling
**Goal**: Consistent error handling and responses

**Tasks**:
- [ ] Create custom exception classes
- [ ] Implement global exception handlers
- [ ] Add structured error responses
- [ ] Add error logging with context
- [ ] Create error response models

**Structure**:
```python
# backend/app/core/exceptions.py
class AppException(Exception):
    """Base application exception"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class ValidationException(AppException):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=400)

# Global exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

#### 1.6 Modernize FastAPI Patterns
**Goal**: Use current best practices

**Tasks**:
- [ ] Replace `@app.on_event` with lifespan context manager
- [ ] Implement proper dependency injection
- [ ] Add response models to all endpoints
- [ ] Enhance OpenAPI documentation
- [ ] Add request/response examples

**Example - Lifespan**:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up AISJ Connect API...")
    await db.connect()
    logger.info("API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down API...")
    await db.close()
    logger.info("API shutdown complete")

app = FastAPI(
    title="AISJ Connect API",
    version="1.0",
    lifespan=lifespan
)
```

---

### Phase 2: Security Enhancements (Priority: High)

#### 2.1 Environment & Secrets Management
**Tasks**:
- [ ] Validate required environment variables on startup
- [ ] Remove all hardcoded secrets
- [ ] Create secure `.env.example`
- [ ] Add secrets rotation documentation
- [ ] Implement environment-based CORS configuration

#### 2.2 Authentication & Authorization
**Tasks**:
- [ ] Implement refresh token mechanism
- [ ] Add token blacklist for logout
- [ ] Implement role-based permission decorators
- [ ] Add password complexity validation
- [ ] Implement account lockout after failed attempts
- [ ] Add JWT token rotation

#### 2.3 Rate Limiting
**Tasks**:
- [ ] Install `slowapi` or similar
- [ ] Add rate limiting to auth endpoints
- [ ] Configure rate limits per endpoint type
- [ ] Add rate limit headers to responses

#### 2.4 Input Validation & Sanitization
**Tasks**:
- [ ] Enhance Pydantic models with strict validation
- [ ] Add input sanitization for text fields
- [ ] Implement request size limits
- [ ] Add file upload validation (for future photo uploads)

---

### Phase 3: Code Quality (Priority: Medium)

#### 3.1 Type Safety
**Tasks**:
- [ ] Add type hints to all functions
- [ ] Add return type annotations
- [ ] Configure mypy for static type checking
- [ ] Create type aliases for common types

#### 3.2 Documentation
**Tasks**:
- [ ] Add docstrings to all functions (Google style)
- [ ] Enhance OpenAPI schema with descriptions
- [ ] Add request/response examples to endpoints
- [ ] Create API usage guide
- [ ] Document authentication flow

#### 3.3 Code Formatting & Linting
**Tasks**:
- [ ] Configure `black` for code formatting
- [ ] Configure `isort` for import sorting
- [ ] Configure `flake8` for linting
- [ ] Configure `pylint` for advanced linting
- [ ] Add pre-commit hooks
- [ ] Create `pyproject.toml` configuration

#### 3.4 Logging
**Tasks**:
- [ ] Implement structured logging
- [ ] Add request/response logging middleware
- [ ] Configure log levels per environment
- [ ] Add correlation IDs for request tracking
- [ ] Implement log rotation

---

### Phase 4: Frontend Refactoring (Priority: Medium)

#### 4.1 API Client Organization
**Tasks**:
- [ ] Create centralized error handling for API calls
- [ ] Implement request/response interceptors
- [ ] Add retry logic for failed requests
- [ ] Implement request cancellation
- [ ] Add loading state management

#### 4.2 Type Safety
**Tasks**:
- [ ] Create shared TypeScript types for API responses
- [ ] Generate types from OpenAPI schema (optional)
- [ ] Add strict TypeScript configuration
- [ ] Remove any `any` types

#### 4.3 Context Optimization
**Tasks**:
- [ ] Review AuthContext for optimization
- [ ] Implement memoization where needed
- [ ] Add context splitting if needed
- [ ] Implement React Query for data fetching (optional)

#### 4.4 Component Structure
**Tasks**:
- [ ] Create reusable component library
- [ ] Implement proper prop typing
- [ ] Add component documentation
- [ ] Create shared constants file

---

### Phase 5: Testing (Priority: High)

See `TESTING_PLAN.md` for comprehensive testing strategy.

---

### Phase 6: Performance & Scalability (Priority: Low)

#### 6.1 Database Optimization
**Tasks**:
- [ ] Review and optimize indexes
- [ ] Implement query result caching
- [ ] Add database query profiling
- [ ] Optimize aggregation pipelines

#### 6.2 API Performance
**Tasks**:
- [ ] Implement response caching
- [ ] Add compression middleware
- [ ] Optimize serialization
- [ ] Add performance monitoring

#### 6.3 Mobile Optimization
**Tasks**:
- [ ] Implement request batching
- [ ] Add offline support
- [ ] Implement optimistic updates
- [ ] Add data prefetching

---

## Implementation Order (Recommended)

### Week 1: Foundation
1. Consolidate database layer (1.1)
2. Centralize configuration (1.2)
3. Improve error handling (1.5)

### Week 2: Architecture
4. Implement service layer (1.3)
5. Implement repository pattern (1.4)
6. Modernize FastAPI patterns (1.6)

### Week 3: Security
7. Environment & secrets management (2.1)
8. Authentication enhancements (2.2)
9. Rate limiting (2.3)

### Week 4: Quality & Testing
10. Type safety improvements (3.1)
11. Documentation (3.2)
12. Testing setup and implementation (Phase 5)

### Week 5: Frontend
13. Frontend refactoring (Phase 4)
14. Code formatting & linting (3.3)

### Week 6: Polish
15. Logging improvements (3.4)
16. Performance optimizations (Phase 6)
17. Final review and cleanup

---

## Success Metrics

- [ ] 100% of code uses consistent patterns
- [ ] All routes have service layer abstraction
- [ ] All database operations use repository pattern
- [ ] Test coverage > 80%
- [ ] No hardcoded secrets or configuration
- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] Zero linting errors
- [ ] Security audit passes
- [ ] Performance benchmarks meet requirements

---

## Risk Mitigation

1. **Breaking Changes**: Use feature branches for each phase
2. **Database Issues**: Test migration scripts in staging environment
3. **Time Overrun**: Prioritize high-priority items first
4. **Regression**: Implement comprehensive test suite before major refactoring
5. **Team Coordination**: Use git branches per phase, regular code reviews

---

## Notes

- All refactoring should be done on feature branches
- Each phase should be reviewed and tested before merging
- Maintain backward compatibility where possible
- Document all breaking changes
- Update ROADMAP.md as phases complete

---

**Last Updated**: December 4, 2025
**Status**: Draft - Ready for Review
