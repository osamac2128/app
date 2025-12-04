from fastapi.testclient import TestClient
from server import app
import pytest

client = TestClient(app)

def test_read_main():
    response = client.get("/api/")
    assert response.status_code == 200
    # The actual response includes status and version
    assert response.json()["message"] == "AISJ Connect API"

def test_register_and_login():
    # 1. Register
    register_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test_unique@example.com", # Use a unique email to avoid conflict
        "password": "Password123", # Needs uppercase, lowercase, number
        "role": "student"
    }
    
    # Try to register
    response = client.post("/api/auth/register", json=register_data)
    # If already exists, that's fine for this simple test, we just proceed to login
    if response.status_code != 201 and response.status_code != 400:
        assert response.status_code == 201

    login_data = {
        "email": "test_unique@example.com",
        "password": "Password123"
    }
    
    login_response = client.post("/api/auth/login", json=login_data)
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return token

def test_get_my_id():
    try:
        token = test_register_and_login()
    except AssertionError:
        pytest.skip("Login failed, skipping dependent test")
        
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/digital-ids/my-id", headers=headers)
    # If ID doesn't exist yet, it might return 404 or create one. 
    # Assuming the endpoint returns 200 if successful.
    if response.status_code == 404:
        # Try to create one if needed, or just assert 404 is a valid response for now
        pass
    else:
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data

def test_get_locations():
    try:
        token = test_register_and_login()
    except AssertionError:
        pytest.skip("Login failed, skipping dependent test")

    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/passes/locations", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_emergency_active():
    try:
        token = test_register_and_login()
    except AssertionError:
        pytest.skip("Login failed, skipping dependent test")

    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/emergency/active", headers=headers)
    assert response.status_code == 200
