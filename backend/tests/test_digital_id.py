"""
Digital ID Module Tests
Tests for digital ID card functionality, photo approval, and scanning.
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


class TestDigitalID:
    """Test suite for Digital ID endpoints."""

    def test_get_my_id_creates_if_not_exists(self):
        """Test getting digital ID creates one if it doesn't exist."""
        token, user_id = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/digital-ids/my-id", headers=headers)

        # Should return 200 with new ID or existing ID
        assert response.status_code == 200
        data = response.json()
        assert "qr_code" in data
        assert "barcode" in data
        assert data["user_id"] == user_id

    def test_digital_id_has_qr_code(self):
        """Test that digital ID includes QR code."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/digital-ids/my-id", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "qr_code" in data
        assert len(data["qr_code"]) > 0

    def test_digital_id_has_barcode(self):
        """Test that digital ID includes barcode."""
        token, _ = get_user_token("student")
        if not token:
            pytest.skip("Could not create test user")

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/digital-ids/my-id", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "barcode" in data
        assert len(data["barcode"]) > 0


class TestIDScanning:
    """Test suite for ID scanning functionality."""

    def test_staff_can_scan_id(self):
        """Test that staff can scan a student's ID."""
        # Create a student and get their ID
        student_token, _ = get_user_token("student")
        if not student_token:
            pytest.skip("Could not create student user")

        # Get the student's digital ID
        student_headers = {"Authorization": f"Bearer {student_token}"}
        id_response = client.get("/api/digital-ids/my-id", headers=student_headers)
        if id_response.status_code != 200:
            pytest.skip("Could not get student ID")

        qr_code = id_response.json()["qr_code"]

        # Create a staff user
        staff_token, _ = get_user_token("staff")
        if not staff_token:
            pytest.skip("Could not create staff user")

        # Staff scans the QR code
        staff_headers = {"Authorization": f"Bearer {staff_token}"}
        scan_response = client.get(f"/api/digital-ids/scan/{qr_code}", headers=staff_headers)

        assert scan_response.status_code == 200
        data = scan_response.json()
        assert data["valid"] is True
        assert "user" in data
        assert "digital_id" in data

    def test_scan_invalid_qr_code(self):
        """Test scanning an invalid QR code returns error."""
        staff_token, _ = get_user_token("staff")
        if not staff_token:
            pytest.skip("Could not create staff user")

        headers = {"Authorization": f"Bearer {staff_token}"}
        response = client.get("/api/digital-ids/scan/invalid_qr_code_12345", headers=headers)

        assert response.status_code == 404

    def test_student_cannot_scan_ids(self):
        """Test that students cannot scan IDs."""
        student_token, _ = get_user_token("student")
        if not student_token:
            pytest.skip("Could not create student user")

        headers = {"Authorization": f"Bearer {student_token}"}
        response = client.get("/api/digital-ids/scan/some_qr_code", headers=headers)

        assert response.status_code == 403


class TestPhotoApproval:
    """Test suite for photo upload and approval workflow."""

    def test_get_pending_photos_staff(self):
        """Test staff can view pending photo approvals."""
        staff_token, _ = get_user_token("staff")
        if not staff_token:
            pytest.skip("Could not create staff user")

        headers = {"Authorization": f"Bearer {staff_token}"}
        response = client.get("/api/digital-ids/admin/pending-photos", headers=headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_student_cannot_view_pending_photos(self):
        """Test students cannot access pending photos endpoint."""
        student_token, _ = get_user_token("student")
        if not student_token:
            pytest.skip("Could not create student user")

        headers = {"Authorization": f"Bearer {student_token}"}
        response = client.get("/api/digital-ids/admin/pending-photos", headers=headers)

        assert response.status_code == 403


class TestScanHistory:
    """Test suite for scan history functionality."""

    def test_staff_can_view_scan_history(self):
        """Test staff can view scan history."""
        staff_token, _ = get_user_token("staff")
        if not staff_token:
            pytest.skip("Could not create staff user")

        headers = {"Authorization": f"Bearer {staff_token}"}
        response = client.get("/api/digital-ids/scan-history", headers=headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_student_cannot_view_scan_history(self):
        """Test students cannot view scan history."""
        student_token, _ = get_user_token("student")
        if not student_token:
            pytest.skip("Could not create student user")

        headers = {"Authorization": f"Bearer {student_token}"}
        response = client.get("/api/digital-ids/scan-history", headers=headers)

        assert response.status_code == 403
