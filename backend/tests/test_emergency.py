"""
Emergency Communications Module Tests
Tests for emergency alerts, templates, and accountability features.
"""

from fastapi.testclient import TestClient
from server import app
import pytest
import uuid

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


class TestEmergencyAlerts:
    """Test suite for emergency alert endpoints."""

    def test_get_active_alert(self):
        """Test checking for active emergency alert."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/active", headers=headers)

        assert response.status_code == 200
        # Response can be null (no active alert) or an alert object

    def test_student_cannot_trigger_alert(self):
        """Test students cannot trigger emergency alerts."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/emergency/trigger", headers=headers, json={
            "type": "lockdown",
            "severity": "high",
            "title": "Test Alert",
            "message": "This is a test"
        })

        assert response.status_code == 403

    def test_staff_cannot_trigger_alert(self):
        """Test staff cannot trigger emergency alerts (admin only)."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/emergency/trigger", headers=headers, json={
            "type": "lockdown",
            "severity": "high",
            "title": "Test Alert",
            "message": "This is a test"
        })

        assert response.status_code == 403


class TestEmergencyTemplates:
    """Test suite for emergency templates."""

    def test_get_all_templates(self):
        """Test getting all emergency templates."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/templates", headers=headers)

        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)
        assert len(templates) > 0

        # Verify template structure
        for template in templates:
            assert "type" in template
            assert "title" in template
            assert "message" in template
            assert "severity" in template

    def test_get_specific_template(self):
        """Test getting a specific emergency template."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/templates/lockdown", headers=headers)

        assert response.status_code == 200
        template = response.json()
        assert template["type"] == "lockdown"
        assert "title" in template
        assert "message" in template

    def test_get_nonexistent_template(self):
        """Test getting a non-existent template returns 404."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/templates/nonexistent_type", headers=headers)

        assert response.status_code == 404

    def test_student_cannot_access_templates(self):
        """Test students cannot access emergency templates."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/templates", headers=headers)

        assert response.status_code == 403

    def test_template_types_coverage(self):
        """Test that all expected template types exist."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/templates", headers=headers)

        assert response.status_code == 200
        templates = response.json()
        template_types = [t["type"] for t in templates]

        # Verify critical templates exist
        expected_types = ["lockdown", "fire", "tornado", "earthquake", "medical", "all_clear"]
        for expected in expected_types:
            assert expected in template_types, f"Missing template type: {expected}"


class TestSmartPassIntegration:
    """Test Smart Pass integration with emergency system."""

    def test_get_active_passes(self):
        """Test getting active passes during emergency."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/active-passes", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "emergency_active" in data
        assert "total_students_out" in data
        assert "passes" in data
        assert isinstance(data["passes"], list)

    def test_student_cannot_view_active_passes(self):
        """Test students cannot view active passes endpoint."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/active-passes", headers=headers)

        assert response.status_code == 403


class TestEmergencyHistory:
    """Test emergency history functionality."""

    def test_get_emergency_history(self):
        """Test getting emergency alert history."""
        token, _ = get_user_token("staff")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/history", headers=headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_student_cannot_view_history(self):
        """Test students cannot view emergency history."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/emergency/history", headers=headers)

        assert response.status_code == 403
