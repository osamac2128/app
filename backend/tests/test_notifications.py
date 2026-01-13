"""
Notifications Module Tests
Tests for push notifications, scheduling, and templates.
"""

from fastapi.testclient import TestClient
from server import app
import pytest
import uuid
from datetime import datetime, timedelta

client = TestClient(app)


def get_user_token(role="student"):
    """Helper to create a user and get token."""
    email = f"{role}_{uuid.uuid4().hex[:8]}@example.com"
    register_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password": "SecurePass123!",
        "role": role
    }
    response = client.post("/api/auth/register", json=register_data)
    if response.status_code in [200, 201]:
        return response.json()["access_token"], response.json()["user"]["_id"]
    return None, None


class TestNotifications:
    """Test suite for notification endpoints."""

    def test_send_notification_staff(self):
        """Test staff can send notifications."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        notification_data = {
            "title": "Test Notification",
            "body": "This is a test notification",
            "type": "announcement",
            "target_roles": None
        }
        response = client.post("/api/notifications/send", headers=headers, json=notification_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Notification"

    def test_student_cannot_send_notification(self):
        """Test students cannot send notifications."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        notification_data = {
            "title": "Test Notification",
            "body": "This is a test notification",
            "type": "announcement"
        }
        response = client.post("/api/notifications/send", headers=headers, json=notification_data)

        assert response.status_code == 403

    def test_get_notifications_list(self):
        """Test getting notifications list."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/notifications/list", headers=headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestNotificationScheduling:
    """Test suite for notification scheduling."""

    def test_schedule_notification(self):
        """Test scheduling a notification for future delivery."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        schedule_data = {
            "title": "Scheduled Test",
            "body": "This is a scheduled notification",
            "type": "announcement",
            "scheduled_for": future_time,
            "priority": "normal"
        }
        response = client.post("/api/notifications/schedule", headers=headers, json=schedule_data)

        assert response.status_code == 200
        data = response.json()
        assert "notification" in data
        assert data["notification"]["status"] == "scheduled"

    def test_schedule_notification_past_time_fails(self):
        """Test scheduling for past time fails."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        schedule_data = {
            "title": "Past Scheduled Test",
            "body": "This should fail",
            "type": "announcement",
            "scheduled_for": past_time,
            "priority": "normal"
        }
        response = client.post("/api/notifications/schedule", headers=headers, json=schedule_data)

        assert response.status_code == 400

    def test_get_scheduled_notifications(self):
        """Test getting list of scheduled notifications."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/notifications/scheduled", headers=headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_student_cannot_schedule(self):
        """Test students cannot schedule notifications."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        schedule_data = {
            "title": "Unauthorized Schedule",
            "body": "This should fail",
            "type": "announcement",
            "scheduled_for": future_time
        }
        response = client.post("/api/notifications/schedule", headers=headers, json=schedule_data)

        assert response.status_code == 403


class TestNotificationTemplates:
    """Test suite for notification templates."""

    def test_get_notification_templates(self):
        """Test getting notification templates."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/notifications/templates", headers=headers)

        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)
        assert len(templates) > 0

        # Verify template structure
        for template in templates:
            assert "name" in template
            assert "title" in template
            assert "body" in template

    def test_student_cannot_access_templates(self):
        """Test students cannot access notification templates."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/notifications/templates", headers=headers)

        assert response.status_code == 403


class TestTargetedNotifications:
    """Test suite for targeted notifications."""

    def test_send_to_students_only(self):
        """Test sending notification to students only."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        notification_data = {
            "title": "Student Announcement",
            "body": "This is for students only",
            "type": "announcement",
            "target_roles": ["student"]
        }
        response = client.post("/api/notifications/send", headers=headers, json=notification_data)

        assert response.status_code == 200
        data = response.json()
        assert data["target_roles"] == ["student"]

    def test_send_to_multiple_roles(self):
        """Test sending notification to multiple roles."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        notification_data = {
            "title": "Staff and Parent Announcement",
            "body": "This is for staff and parents",
            "type": "announcement",
            "target_roles": ["staff", "parent"]
        }
        response = client.post("/api/notifications/send", headers=headers, json=notification_data)

        assert response.status_code == 200
