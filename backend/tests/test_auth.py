"""
Authentication Module Tests
Tests for JWT auth, registration, login, and role-based access control.
"""

from fastapi.testclient import TestClient
from server import app
import pytest
import uuid

client = TestClient(app)


class TestAuthentication:
    """Test suite for authentication endpoints."""

    @pytest.fixture
    def unique_email(self):
        """Generate a unique email for each test."""
        return f"test_{uuid.uuid4().hex[:8]}@example.com"

    def test_register_valid_user(self, unique_email):
        """Test successful user registration."""
        register_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "password": "SecurePass123!",
            "role": "student"
        }
        response = client.post("/api/auth/register", json=register_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == unique_email

    def test_register_weak_password(self, unique_email):
        """Test registration with weak password fails."""
        register_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "password": "weak",
            "role": "student"
        }
        response = client.post("/api/auth/register", json=register_data)
        assert response.status_code == 400

    def test_register_invalid_email(self):
        """Test registration with invalid email fails."""
        register_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "not-an-email",
            "password": "SecurePass123!",
            "role": "student"
        }
        response = client.post("/api/auth/register", json=register_data)
        assert response.status_code == 422

    def test_register_duplicate_email(self, unique_email):
        """Test duplicate email registration fails."""
        register_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "password": "SecurePass123!",
            "role": "student"
        }
        # First registration
        client.post("/api/auth/register", json=register_data)
        # Second registration with same email
        response = client.post("/api/auth/register", json=register_data)
        assert response.status_code == 400

    def test_login_valid_credentials(self, unique_email):
        """Test successful login."""
        # Register first
        register_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "password": "SecurePass123!",
            "role": "student"
        }
        client.post("/api/auth/register", json=register_data)

        # Login
        login_data = {
            "email": unique_email,
            "password": "SecurePass123!"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data

    def test_login_invalid_password(self, unique_email):
        """Test login with wrong password fails."""
        # Register first
        register_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "password": "SecurePass123!",
            "role": "student"
        }
        client.post("/api/auth/register", json=register_data)

        # Login with wrong password
        login_data = {
            "email": unique_email,
            "password": "WrongPassword123!"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login with non-existent email fails."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SecurePass123!"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    def test_get_current_user(self, unique_email):
        """Test getting current user profile."""
        # Register and login
        register_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "password": "SecurePass123!",
            "role": "student"
        }
        reg_response = client.post("/api/auth/register", json=register_data)
        token = reg_response.json()["access_token"]

        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == unique_email

    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token fails."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_invalid_token(self):
        """Test accessing protected endpoint with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401


class TestRoleBasedAccess:
    """Test role-based access control."""

    @pytest.fixture
    def student_token(self):
        """Get a student user token."""
        email = f"student_{uuid.uuid4().hex[:8]}@example.com"
        register_data = {
            "first_name": "Student",
            "last_name": "User",
            "email": email,
            "password": "SecurePass123!",
            "role": "student"
        }
        response = client.post("/api/auth/register", json=register_data)
        if response.status_code in [200, 201]:
            return response.json()["access_token"]
        # If registration fails, try login
        login_response = client.post("/api/auth/login", json={
            "email": email,
            "password": "SecurePass123!"
        })
        return login_response.json()["access_token"]

    @pytest.fixture
    def staff_token(self):
        """Get a staff user token."""
        email = f"staff_{uuid.uuid4().hex[:8]}@example.com"
        register_data = {
            "first_name": "Staff",
            "last_name": "User",
            "email": email,
            "password": "SecurePass123!",
            "role": "staff"
        }
        response = client.post("/api/auth/register", json=register_data)
        if response.status_code in [200, 201]:
            return response.json()["access_token"]
        login_response = client.post("/api/auth/login", json={
            "email": email,
            "password": "SecurePass123!"
        })
        return login_response.json()["access_token"]

    def test_student_cannot_trigger_emergency(self, student_token):
        """Test students cannot trigger emergency alerts."""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = client.post("/api/emergency/trigger", headers=headers, json={
            "type": "lockdown",
            "severity": "high",
            "title": "Test",
            "message": "Test"
        })
        assert response.status_code == 403

    def test_staff_can_view_templates(self, staff_token):
        """Test staff can view emergency templates."""
        headers = {"Authorization": f"Bearer {staff_token}"}
        response = client.get("/api/emergency/templates", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
