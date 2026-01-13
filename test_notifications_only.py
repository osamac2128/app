#!/usr/bin/env python3
"""
Quick test for Admin Messages/Announcements feature only
"""

import requests
import json

# Configuration
BASE_URL = "https://missing-links-fix-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "osama.chaudhry@gmail.com"
ADMIN_PASSWORD = "Test12345"

def authenticate():
    """Get admin token"""
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    else:
        print(f"❌ Authentication failed: {response.status_code} - {response.text}")
        return None

def test_all_scenarios(headers):
    """Test all notification scenarios"""
    results = []
    
    # Scenario 1: Send announcement to all users
    print("Scenario 1: Send announcement to all users...")
    notification_data = {
        "title": "School Assembly Tomorrow",
        "body": "All students and staff are required to attend the assembly at 9 AM tomorrow.",
        "type": "announcement",
        "target_roles": None  # All users
    }
    
    response = requests.post(f"{BASE_URL}/notifications/send", json=notification_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Notification sent with ID: {data.get('_id')}")
        results.append(("Scenario 1 - All Users", True, data.get('_id')))
    else:
        print(f"❌ FAILED: {response.text}")
        results.append(("Scenario 1 - All Users", False, response.text))
    
    # Scenario 2: Send urgent alert to students only
    print("\nScenario 2: Send urgent alert to students...")
    urgent_data = {
        "title": "Class Cancelled",
        "body": "Math class is cancelled today due to teacher absence.",
        "type": "urgent",
        "target_roles": ["student"]
    }
    
    response = requests.post(f"{BASE_URL}/notifications/send", json=urgent_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Urgent alert sent with ID: {data.get('_id')}")
        results.append(("Scenario 2 - Students Only", True, data.get('_id')))
    else:
        print(f"❌ FAILED: {response.text}")
        results.append(("Scenario 2 - Students Only", False, response.text))
    
    # Scenario 3: Send reminder to staff
    print("\nScenario 3: Send reminder to staff...")
    reminder_data = {
        "title": "Staff Meeting Reminder",
        "body": "Don't forget the staff meeting at 3 PM in the conference room.",
        "type": "reminder",
        "target_roles": ["staff"]
    }
    
    response = requests.post(f"{BASE_URL}/notifications/send", json=reminder_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Staff reminder sent with ID: {data.get('_id')}")
        results.append(("Scenario 3 - Staff Only", True, data.get('_id')))
    else:
        print(f"❌ FAILED: {response.text}")
        results.append(("Scenario 3 - Staff Only", False, response.text))
    
    return results

def test_fetch_sent(headers):
    """Test fetching sent notifications"""
    print("\nTesting: Fetch sent notifications...")
    
    response = requests.get(f"{BASE_URL}/notifications/sent", headers=headers)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Retrieved {len(data)} notifications")
        if data:
            print(f"Sample notification: {data[0]}")
    else:
        print(f"❌ FAILED: {response.text}")

def test_error_cases(headers):
    """Test error cases"""
    print("\n" + "="*50)
    print("TESTING ERROR CASES")
    print("="*50)
    
    # Test 1: Missing required fields
    print("Error Test 1: Missing required fields...")
    invalid_data = {
        "type": "announcement"
        # Missing title and body
    }
    
    response = requests.post(f"{BASE_URL}/notifications/send", json=invalid_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code in [400, 422]:
        print("✅ SUCCESS: Correctly rejected invalid data")
    else:
        print(f"❌ FAILED: Should have rejected invalid data but got {response.status_code}")
    
    # Test 2: Invalid authentication
    print("\nError Test 2: Invalid authentication...")
    headers_no_auth = {"Content-Type": "application/json"}
    
    valid_data = {
        "title": "Test",
        "body": "Test message",
        "type": "general"
    }
    
    response = requests.post(f"{BASE_URL}/notifications/send", json=valid_data, headers=headers_no_auth)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ SUCCESS: Correctly rejected unauthorized request")
    else:
        print(f"❌ FAILED: Should have rejected unauthorized request but got {response.status_code}")

def main():
    print("🧪 Testing Admin Messages/Announcements API")
    print("=" * 50)
    
    # Authenticate
    headers = authenticate()
    if not headers:
        return
    
    print("✅ Authentication successful")
    
    # Test all scenarios
    results = test_all_scenarios(headers)
    
    # Test fetching sent notifications
    test_fetch_sent(headers)
    
    # Test error cases
    test_error_cases(headers)
    
    # Summary
    print("\n" + "="*50)
    print("FINAL SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"Scenarios Passed: {passed}/{total}")
    
    for scenario, success, details in results:
        status = "✅" if success else "❌"
        print(f"{status} {scenario}")
    
    if passed == total:
        print("\n🎉 ALL ADMIN MESSAGES/ANNOUNCEMENTS TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")

if __name__ == "__main__":
    main()