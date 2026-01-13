# AISJ Connect - Comprehensive Testing Plan

## Executive Summary

This document outlines a complete testing strategy for the AISJ Connect application, covering backend API testing, frontend component testing, integration testing, end-to-end testing, performance testing, and security testing. The goal is to achieve >80% code coverage and ensure all features work correctly across all user roles.

---

## Testing Philosophy

1. **Test Pyramid Approach**: More unit tests, fewer integration tests, minimal E2E tests
2. **Test-Driven Development**: Write tests before or alongside code
3. **Automated Testing**: All tests should be automated and run in CI/CD
4. **Role-Based Testing**: Test all features for each user role (Student, Parent, Staff, Admin)
5. **Continuous Testing**: Tests run on every commit

---

## Testing Infrastructure Setup

### Backend Testing Tools

**Required Packages**:
```bash
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
httpx>=0.24.0
faker>=19.0.0
factory-boy>=3.3.0
```

**Configuration** (`pytest.ini`):
```ini
[pytest]
testpaths = backend/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    --cov=backend/app
    --cov=backend/utils
    --cov=backend/routes
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v
    --tb=short
```

### Frontend Testing Tools

**Required Packages**:
```bash
@testing-library/react-native
@testing-library/jest-native
jest
jest-expo
@types/jest
```

**Configuration** (`jest.config.js`):
```javascript
module.exports = {
  preset: 'jest-expo',
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg)'
  ],
  collectCoverage: true,
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'api/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'contexts/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 75,
      lines: 80,
      statements: 80,
    },
  },
};
```

---

## Backend Testing Strategy

### 1. Unit Tests

#### 1.1 Service Layer Tests

**Location**: `backend/tests/unit/services/`

**Test Files**:
- `test_auth_service.py`
- `test_digital_id_service.py`
- `test_pass_service.py`
- `test_emergency_service.py`
- `test_notification_service.py`
- `test_visitor_service.py`

**Example Test Structure** (`test_auth_service.py`):
```python
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.auth_service import AuthService
from app.core.exceptions import UnauthorizedException, ValidationException

class TestAuthService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def auth_service(self, mock_db):
        return AuthService(mock_db)

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_db):
        """Test successful user registration"""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "Password123",
            "first_name": "Test",
            "last_name": "User",
            "role": "student"
        }
        mock_db.users.find_one.return_value = None
        mock_db.users.insert_one.return_value = Mock(inserted_id="123")

        # Act
        result = await auth_service.register_user(user_data)

        # Assert
        assert result["email"] == "test@example.com"
        mock_db.users.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, mock_db):
        """Test registration with duplicate email fails"""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "Password123",
            "first_name": "Test",
            "last_name": "User",
            "role": "student"
        }
        mock_db.users.find_one.return_value = {"email": "test@example.com"}

        # Act & Assert
        with pytest.raises(ValidationException):
            await auth_service.register_user(user_data)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_db):
        """Test successful authentication"""
        # Test implementation
        pass

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, auth_service, mock_db):
        """Test authentication with invalid credentials fails"""
        # Test implementation
        pass

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive_account(self, auth_service, mock_db):
        """Test authentication with inactive account fails"""
        # Test implementation
        pass
```

**Coverage Requirements**:
- [ ] All service methods have tests
- [ ] Success cases tested
- [ ] All error cases tested
- [ ] Edge cases tested
- [ ] Mock database properly
- [ ] Test business logic thoroughly

---

#### 1.2 Repository Layer Tests

**Location**: `backend/tests/unit/repositories/`

**Test Files**:
- `test_base_repository.py`
- `test_user_repository.py`
- `test_pass_repository.py`
- `test_digital_id_repository.py`

**Example**:
```python
class TestUserRepository:
    @pytest.mark.asyncio
    async def test_find_by_email(self):
        """Test finding user by email"""
        pass

    @pytest.mark.asyncio
    async def test_create_user(self):
        """Test creating a new user"""
        pass

    @pytest.mark.asyncio
    async def test_update_user(self):
        """Test updating user data"""
        pass
```

---

#### 1.3 Utility Function Tests

**Location**: `backend/tests/unit/utils/`

**Test Files**:
- `test_auth_utils.py`
- `test_dependencies.py`

**Example** (`test_auth_utils.py`):
```python
class TestAuthUtils:
    def test_password_hashing(self):
        """Test password hashing works correctly"""
        from utils.auth import get_password_hash, verify_password

        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_jwt_token_creation(self):
        """Test JWT token creation and decoding"""
        from utils.auth import create_access_token, decode_access_token

        data = {"sub": "user123", "role": "student"}
        token = create_access_token(data)

        decoded = decode_access_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "student"

    def test_jwt_token_expiration(self):
        """Test JWT token expiration handling"""
        pass
```

---

### 2. Integration Tests

#### 2.1 API Endpoint Tests

**Location**: `backend/tests/integration/`

**Test Files**:
- `test_auth_routes.py`
- `test_digital_id_routes.py`
- `test_pass_routes.py`
- `test_emergency_routes.py`
- `test_notification_routes.py`
- `test_visitor_routes.py`

**Example** (`test_auth_routes.py`):
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

class TestAuthRoutes:
    @pytest.mark.asyncio
    async def test_register_endpoint(self, client):
        """Test /api/auth/register endpoint"""
        response = await client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "password": "Password123",
            "first_name": "New",
            "last_name": "User",
            "role": "student"
        })

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client):
        """Test registration with duplicate email returns 400"""
        # First registration
        await client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Password123",
            "first_name": "First",
            "last_name": "User",
            "role": "student"
        })

        # Duplicate registration
        response = await client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Password123",
            "first_name": "Second",
            "last_name": "User",
            "role": "student"
        })

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_endpoint(self, client):
        """Test /api/auth/login endpoint"""
        # Register user first
        await client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "Password123",
            "first_name": "Login",
            "last_name": "User",
            "role": "student"
        })

        # Login
        response = await client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "Password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials returns 401"""
        response = await client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword"
        })

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client):
        """Test /api/auth/me endpoint"""
        # Register and login
        reg_response = await client.post("/api/auth/register", json={
            "email": "me@example.com",
            "password": "Password123",
            "first_name": "Me",
            "last_name": "User",
            "role": "student"
        })
        token = reg_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
```

---

#### 2.2 Database Integration Tests

**Location**: `backend/tests/integration/database/`

**Test Files**:
- `test_database_connection.py`
- `test_indexes.py`
- `test_seed_data.py`

**Example**:
```python
class TestDatabaseIntegration:
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test database connection is successful"""
        from app.core.database import db
        await db.connect()
        assert db.db is not None
        await db.close()

    @pytest.mark.asyncio
    async def test_indexes_created(self):
        """Test all required indexes are created"""
        from app.core.database import db
        await db.connect()

        # Check users collection indexes
        indexes = await db.db.users.index_information()
        assert "email_1" in indexes
        assert "role_1" in indexes

        await db.close()
```

---

### 3. Functional Tests by Module

#### 3.1 Digital ID Module Tests

**File**: `backend/tests/functional/test_digital_id_module.py`

**Test Cases**:
```python
class TestDigitalIDModule:
    """
    Test all Digital ID functionality for all user roles
    """

    @pytest.mark.asyncio
    async def test_student_can_view_own_id(self):
        """Student can view their own digital ID"""
        pass

    @pytest.mark.asyncio
    async def test_student_cannot_view_other_id(self):
        """Student cannot view another student's ID"""
        pass

    @pytest.mark.asyncio
    async def test_staff_can_scan_student_id(self):
        """Staff can scan and verify student ID"""
        pass

    @pytest.mark.asyncio
    async def test_admin_can_deactivate_id(self):
        """Admin can deactivate a user's digital ID"""
        pass

    @pytest.mark.asyncio
    async def test_admin_can_activate_id(self):
        """Admin can activate a deactivated ID"""
        pass

    @pytest.mark.asyncio
    async def test_scan_creates_log_entry(self):
        """ID scan creates audit log entry"""
        pass

    @pytest.mark.asyncio
    async def test_qr_code_generation(self):
        """QR code is generated correctly"""
        pass

    @pytest.mark.asyncio
    async def test_barcode_generation(self):
        """Barcode is generated correctly"""
        pass
```

---

#### 3.2 Smart Pass Module Tests

**File**: `backend/tests/functional/test_smart_pass_module.py`

**Test Cases**:
```python
class TestSmartPassModule:
    """
    Test all Smart Pass functionality
    """

    @pytest.mark.asyncio
    async def test_student_can_request_pass(self):
        """Student can request a hall pass"""
        pass

    @pytest.mark.asyncio
    async def test_cannot_have_multiple_active_passes(self):
        """Student cannot have multiple active passes"""
        pass

    @pytest.mark.asyncio
    async def test_pass_time_limit_enforced(self):
        """Pass time limit is correctly enforced"""
        pass

    @pytest.mark.asyncio
    async def test_pass_overtime_flagged(self):
        """Pass is flagged as overtime after time limit"""
        pass

    @pytest.mark.asyncio
    async def test_staff_can_approve_pass(self):
        """Staff can approve pending pass"""
        pass

    @pytest.mark.asyncio
    async def test_staff_can_deny_pass(self):
        """Staff can deny pending pass"""
        pass

    @pytest.mark.asyncio
    async def test_location_capacity_limit(self):
        """Location capacity limit prevents new passes"""
        pass

    @pytest.mark.asyncio
    async def test_encounter_prevention(self):
        """Encounter groups prevent conflicting passes"""
        pass

    @pytest.mark.asyncio
    async def test_no_fly_time_restriction(self):
        """No-fly times prevent pass creation"""
        pass

    @pytest.mark.asyncio
    async def test_student_can_end_pass(self):
        """Student can end their own active pass"""
        pass

    @pytest.mark.asyncio
    async def test_admin_can_view_all_active_passes(self):
        """Admin can view all active passes (hall monitor)"""
        pass

    @pytest.mark.asyncio
    async def test_pass_history_tracking(self):
        """Pass history is tracked correctly"""
        pass
```

---

#### 3.3 Emergency Communications Tests

**File**: `backend/tests/functional/test_emergency_module.py`

**Test Cases**:
```python
class TestEmergencyModule:
    """
    Test all Emergency Communications functionality
    """

    @pytest.mark.asyncio
    async def test_admin_can_trigger_lockdown(self):
        """Admin can trigger lockdown alert"""
        pass

    @pytest.mark.asyncio
    async def test_admin_can_trigger_evacuation(self):
        """Admin can trigger evacuation alert"""
        pass

    @pytest.mark.asyncio
    async def test_all_users_receive_emergency_alert(self):
        """All users receive emergency alert"""
        pass

    @pytest.mark.asyncio
    async def test_user_can_check_in_during_emergency(self):
        """User can check-in during emergency"""
        pass

    @pytest.mark.asyncio
    async def test_admin_can_view_check_in_status(self):
        """Admin can view who has checked in"""
        pass

    @pytest.mark.asyncio
    async def test_admin_can_resolve_emergency(self):
        """Admin can send all-clear and resolve emergency"""
        pass

    @pytest.mark.asyncio
    async def test_only_one_active_emergency(self):
        """Only one emergency can be active at a time"""
        pass

    @pytest.mark.asyncio
    async def test_student_cannot_trigger_emergency(self):
        """Student cannot trigger emergency alert"""
        pass

    @pytest.mark.asyncio
    async def test_drill_mode_works(self):
        """Drill mode emergency works correctly"""
        pass
```

---

#### 3.4 Notification Module Tests

**File**: `backend/tests/functional/test_notification_module.py`

**Test Cases**:
```python
class TestNotificationModule:
    """
    Test all Notification functionality
    """

    @pytest.mark.asyncio
    async def test_admin_can_create_notification(self):
        """Admin can create and send notification"""
        pass

    @pytest.mark.asyncio
    async def test_targeted_notification_by_role(self):
        """Notification can target specific roles"""
        pass

    @pytest.mark.asyncio
    async def test_targeted_notification_by_grade(self):
        """Notification can target specific grades"""
        pass

    @pytest.mark.asyncio
    async def test_scheduled_notification(self):
        """Notification can be scheduled for future"""
        pass

    @pytest.mark.asyncio
    async def test_user_receives_notification(self):
        """User receives notification correctly"""
        pass

    @pytest.mark.asyncio
    async def test_user_can_mark_notification_read(self):
        """User can mark notification as read"""
        pass

    @pytest.mark.asyncio
    async def test_delivery_receipt_tracking(self):
        """Notification delivery is tracked"""
        pass

    @pytest.mark.asyncio
    async def test_notification_template_usage(self):
        """Notification template can be used"""
        pass
```

---

#### 3.5 Visitor Management Tests

**File**: `backend/tests/functional/test_visitor_module.py`

**Test Cases**:
```python
class TestVisitorModule:
    """
    Test all Visitor Management functionality
    """

    @pytest.mark.asyncio
    async def test_visitor_check_in(self):
        """Visitor can check in"""
        pass

    @pytest.mark.asyncio
    async def test_visitor_check_out(self):
        """Visitor can check out"""
        pass

    @pytest.mark.asyncio
    async def test_visitor_badge_generation(self):
        """Visitor badge is generated"""
        pass

    @pytest.mark.asyncio
    async def test_host_notification_on_arrival(self):
        """Host is notified when visitor arrives"""
        pass

    @pytest.mark.asyncio
    async def test_watchlist_alert(self):
        """Watchlist visitor triggers alert"""
        pass

    @pytest.mark.asyncio
    async def test_visitor_pre_registration(self):
        """Visitor can be pre-registered"""
        pass

    @pytest.mark.asyncio
    async def test_admin_can_view_active_visitors(self):
        """Admin can view all active visitors"""
        pass

    @pytest.mark.asyncio
    async def test_visitor_history_tracking(self):
        """Visitor history is tracked"""
        pass
```

---

### 4. Test Fixtures and Factories

**Location**: `backend/tests/fixtures/`

**Files**:
- `conftest.py` - Pytest configuration and shared fixtures
- `factories.py` - Factory Boy factories for test data

**Example** (`conftest.py`):
```python
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.database import db
from motor.motor_asyncio import AsyncIOMotorClient

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_db():
    """Provide clean test database for each test"""
    # Connect to test database
    test_client = AsyncIOMotorClient("mongodb://localhost:27017")
    test_db = test_client["test_aisj_connect"]

    # Clear all collections
    for collection in await test_db.list_collection_names():
        await test_db[collection].delete_many({})

    yield test_db

    # Cleanup
    await test_client.drop_database("test_aisj_connect")
    test_client.close()

@pytest.fixture
async def client():
    """Provide HTTP client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def student_user(test_db):
    """Create a test student user"""
    from utils.auth import get_password_hash
    user = {
        "email": "student@test.com",
        "password_hash": get_password_hash("Password123"),
        "first_name": "Test",
        "last_name": "Student",
        "role": "student",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.users.insert_one(user)
    user["_id"] = str(result.inserted_id)
    return user

@pytest.fixture
async def staff_user(test_db):
    """Create a test staff user"""
    from utils.auth import get_password_hash
    user = {
        "email": "staff@test.com",
        "password_hash": get_password_hash("Password123"),
        "first_name": "Test",
        "last_name": "Staff",
        "role": "staff",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.users.insert_one(user)
    user["_id"] = str(result.inserted_id)
    return user

@pytest.fixture
async def admin_user(test_db):
    """Create a test admin user"""
    from utils.auth import get_password_hash
    user = {
        "email": "admin@test.com",
        "password_hash": get_password_hash("Password123"),
        "first_name": "Test",
        "last_name": "Admin",
        "role": "admin",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await test_db.users.insert_one(user)
    user["_id"] = str(result.inserted_id)
    return user

@pytest.fixture
async def authenticated_client(client, student_user):
    """Provide authenticated HTTP client"""
    from utils.auth import create_access_token
    token = create_access_token({"sub": student_user["_id"], "role": "student"})
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
```

**Example** (`factories.py`):
```python
from faker import Faker
from datetime import datetime
import factory
from utils.auth import get_password_hash

fake = Faker()

class UserFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "email": fake.email(),
            "password_hash": get_password_hash("Password123"),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "role": "student",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults

class PassFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "student_id": fake.uuid4(),
            "origin_location_id": fake.uuid4(),
            "destination_location_id": fake.uuid4(),
            "status": "active",
            "requested_at": datetime.utcnow(),
            "time_limit_minutes": 5,
            "is_overtime": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        defaults.update(kwargs)
        return defaults
```

---

## Frontend Testing Strategy

### 1. Component Tests

**Location**: `frontend/__tests__/components/`

**Test Files**:
- `EmergencyOverlay.test.tsx`
- `PassTimer.test.tsx`

**Example**:
```typescript
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import PassTimer from '@/components/PassTimer';

describe('PassTimer Component', () => {
  it('renders correctly with time remaining', () => {
    const { getByText } = render(
      <PassTimer
        startTime={new Date()}
        timeLimitMinutes={5}
        onTimeExpired={() => {}}
      />
    );

    expect(getByText(/4:/)).toBeTruthy();
  });

  it('calls onTimeExpired when time runs out', () => {
    jest.useFakeTimers();
    const onTimeExpired = jest.fn();

    render(
      <PassTimer
        startTime={new Date(Date.now() - 5 * 60 * 1000)}
        timeLimitMinutes={5}
        onTimeExpired={onTimeExpired}
      />
    );

    expect(onTimeExpired).toHaveBeenCalled();
  });
});
```

---

### 2. Screen Tests

**Location**: `frontend/__tests__/screens/`

**Test Files**:
- `login.test.tsx`
- `register.test.tsx`
- `home.test.tsx`
- `id-card.test.tsx`
- `smart-pass.test.tsx`

---

### 3. API Integration Tests

**Location**: `frontend/__tests__/api/`

**Test Files**:
- `auth.test.ts`
- `passes.test.ts`
- `digitalIds.test.ts`

**Example**:
```typescript
import { authApi } from '@/api/auth';
import MockAdapter from 'axios-mock-adapter';
import client from '@/api/client';

describe('Auth API', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(client);
  });

  afterEach(() => {
    mock.restore();
  });

  it('login returns token on success', async () => {
    const mockResponse = {
      access_token: 'test_token',
      token_type: 'bearer',
      user: { email: 'test@example.com' }
    };

    mock.onPost('/api/auth/login').reply(200, mockResponse);

    const result = await authApi.login({
      email: 'test@example.com',
      password: 'Password123'
    });

    expect(result.access_token).toBe('test_token');
  });
});
```

---

### 4. Context Tests

**Location**: `frontend/__tests__/contexts/`

**Test Files**:
- `AuthContext.test.tsx`

---

## End-to-End Testing

### E2E Testing Tools

**Tools**: Detox or Maestro

**Test Scenarios**:

1. **User Registration Flow**
   - User opens app
   - Clicks register
   - Fills form
   - Submits
   - Sees home screen

2. **Login Flow**
   - User opens app
   - Enters credentials
   - Logs in
   - Sees home screen

3. **Digital ID Flow**
   - User logs in
   - Navigates to ID card
   - Sees QR code
   - Can view ID

4. **Smart Pass Flow**
   - Student logs in
   - Requests pass
   - Sees active pass
   - Timer counts down
   - Ends pass

5. **Emergency Alert Flow**
   - Admin triggers alert
   - All users receive alert
   - Users can check in
   - Admin resolves alert

---

## Performance Testing

### Backend Performance Tests

**Tools**: Locust or Apache JMeter

**Test Scenarios**:
```python
from locust import HttpUser, task, between

class AISJConnectUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before tests"""
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "Password123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def view_digital_id(self):
        """Test viewing digital ID"""
        self.client.get("/api/digital-ids/my-id", headers=self.headers)

    @task(2)
    def get_locations(self):
        """Test getting locations"""
        self.client.get("/api/passes/locations", headers=self.headers)

    @task(1)
    def request_pass(self):
        """Test requesting a pass"""
        self.client.post("/api/passes/request",
            json={
                "origin_location_id": "123",
                "destination_location_id": "456",
                "time_limit_minutes": 5
            },
            headers=self.headers
        )
```

**Performance Criteria**:
- [ ] Login endpoint: < 500ms response time
- [ ] Digital ID retrieval: < 200ms
- [ ] Pass request: < 300ms
- [ ] Emergency alert trigger: < 100ms
- [ ] API can handle 1000 concurrent users
- [ ] Database queries: < 100ms

---

## Security Testing

### Security Test Cases

1. **Authentication Security**
   - [ ] Weak passwords are rejected
   - [ ] SQL/NoSQL injection attempts fail
   - [ ] JWT tokens expire correctly
   - [ ] Invalid tokens are rejected
   - [ ] Rate limiting works on auth endpoints

2. **Authorization Security**
   - [ ] Students cannot access admin endpoints
   - [ ] Users cannot view other users' private data
   - [ ] Role-based access control works correctly

3. **Input Validation**
   - [ ] XSS attempts are sanitized
   - [ ] Large payloads are rejected
   - [ ] Invalid data types are rejected

4. **API Security**
   - [ ] CORS is properly configured
   - [ ] HTTPS is enforced (in production)
   - [ ] Security headers are present

**Tools**:
- OWASP ZAP for automated security testing
- Manual penetration testing
- Dependency vulnerability scanning (Safety, Snyk)

---

## Test Execution Plan

### Local Development

```bash
# Backend tests
cd backend
pytest

# Backend tests with coverage
pytest --cov

# Run specific test file
pytest tests/unit/services/test_auth_service.py

# Frontend tests
cd frontend
npm test

# Frontend with coverage
npm test -- --coverage
```

### CI/CD Pipeline

**GitHub Actions Workflow** (`.github/workflows/test.yml`):
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      mongodb:
        image: mongo:6
        ports:
          - 27017:27017

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm install

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
```

---

## Test Data Management

### Test Database

- Use separate MongoDB instance for testing
- Database name: `test_aisj_connect`
- Clear database before each test run
- Seed with minimal required data

### Test Users

Create standard test users:
```python
TEST_USERS = {
    "student": {
        "email": "student@test.com",
        "password": "TestPassword123",
        "role": "student"
    },
    "parent": {
        "email": "parent@test.com",
        "password": "TestPassword123",
        "role": "parent"
    },
    "staff": {
        "email": "staff@test.com",
        "password": "TestPassword123",
        "role": "staff"
    },
    "admin": {
        "email": "admin@test.com",
        "password": "TestPassword123",
        "role": "admin"
    }
}
```

---

## Coverage Requirements

### Minimum Coverage Targets

- **Overall**: 80%
- **Services**: 90%
- **Repositories**: 85%
- **Routes**: 80%
- **Utilities**: 95%
- **Models**: 70% (mostly validation logic)

### Coverage Exclusions

- Migration scripts
- Database seed scripts
- Development-only code
- Third-party integrations (test with mocks)

---

## Testing Checklist

### Before Each Release

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All functional tests pass
- [ ] Code coverage meets requirements
- [ ] E2E tests pass
- [ ] Performance tests pass
- [ ] Security scan passes
- [ ] No critical bugs in issue tracker
- [ ] Manual testing of new features
- [ ] Regression testing of existing features
- [ ] Test on iOS device
- [ ] Test on Android device
- [ ] Test with different user roles
- [ ] Test offline functionality
- [ ] Test with poor network conditions

---

## Continuous Improvement

### Monthly Review

- Review test coverage trends
- Identify untested code paths
- Update test cases for new features
- Remove obsolete tests
- Optimize slow tests
- Review and update test documentation

### Metrics to Track

- Test execution time
- Code coverage percentage
- Number of tests
- Test failure rate
- Bug escape rate (bugs found in production)
- Time to fix failing tests

---

## Appendix

### Test Naming Conventions

**Format**: `test_<function_name>_<scenario>_<expected_result>`

**Examples**:
- `test_register_user_with_valid_data_returns_token`
- `test_login_with_invalid_password_returns_401`
- `test_request_pass_with_active_pass_fails`

### Test Organization

```
backend/
  tests/
    unit/
      services/
      repositories/
      utils/
    integration/
      routes/
      database/
    functional/
    fixtures/
      conftest.py
      factories.py
    __init__.py

frontend/
  __tests__/
    components/
    screens/
    api/
    contexts/
    utils/
```

---

**Last Updated**: December 4, 2025
**Status**: Draft - Ready for Implementation
**Next Steps**: Begin implementing test infrastructure and unit tests
