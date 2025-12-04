#!/usr/bin/env python3
"""
AISJ Connect Backend API Testing Suite
Tests all backend endpoints comprehensively
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class AISJBackendTester:
    def __init__(self):
        # Use the production URL from frontend/.env
        self.base_url = "https://pull-create-app.preview.emergentagent.com/api"
        self.auth_token = None
        self.current_user = None
        self.test_results = {
            "authentication": {},
            "digital_ids": {},
            "passes": {},
            "notifications": {},
            "emergency": {},
            "summary": {"passed": 0, "failed": 0, "errors": []}
        }
        
        # Test user data
        self.test_user = {
            "email": "sarah.johnson@aisj.edu.sg",
            "password": "SecurePass123!",
            "first_name": "Sarah",
            "last_name": "Johnson", 
            "role": "student",
            "phone": "+65 9123 4567"
        }
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def log_result(self, category: str, test_name: str, success: bool, details: Any = None, error: str = None):
        """Log test result"""
        result = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "error": error
        }
        
        self.test_results[category][test_name] = result
        
        if success:
            self.test_results["summary"]["passed"] += 1
            print(f"✅ {category}.{test_name}: PASSED")
        else:
            self.test_results["summary"]["failed"] += 1
            self.test_results["summary"]["errors"].append(f"{category}.{test_name}: {error}")
            print(f"❌ {category}.{test_name}: FAILED - {error}")
            
        if details:
            print(f"   Details: {details}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, files: Dict = None, 
                    auth_required: bool = True) -> tuple[bool, Any, str]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
            
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                if files:
                    # For file uploads, don't use session headers that might interfere
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            else:
                return False, None, f"Unsupported method: {method}"
                
            if response.status_code < 400:
                try:
                    return True, response.json(), None
                except:
                    return True, response.text, None
            else:
                try:
                    error_data = response.json()
                    return False, error_data, f"HTTP {response.status_code}: {error_data.get('error', error_data.get('detail', 'Unknown error'))}"
                except:
                    return False, response.text, f"HTTP {response.status_code}: {response.text}"
                    
        except requests.exceptions.ConnectionError as e:
            return False, None, f"Connection error: {str(e)}"
        except requests.exceptions.Timeout as e:
            return False, None, f"Timeout error: {str(e)}"
        except Exception as e:
            return False, None, f"Request error: {str(e)}"

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        success, data, error = self.make_request('GET', '/', auth_required=False)
        self.log_result("authentication", "root_endpoint", success, 
                       data.get('message') if success else None, error)
        
        # Test health endpoint
        success, data, error = self.make_request('GET', '/health', auth_required=False)
        self.log_result("authentication", "health_check", success,
                       data.get('status') if success else None, error)

    def test_authentication_flow(self):
        """Test complete authentication flow"""
        print("\n🔐 Testing Authentication Flow...")
        
        # 1. Test Registration
        success, data, error = self.make_request('POST', '/auth/register', 
                                                self.test_user, auth_required=False)
        
        if success:
            self.auth_token = data.get('access_token')
            self.current_user = data.get('user')
            
        self.log_result("authentication", "register", success, 
                       f"User ID: {data.get('user', {}).get('_id')}" if success else None, error)
        
        # 2. Test Login (even if registration failed, try with existing user)
        login_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        
        success, data, error = self.make_request('POST', '/auth/login', 
                                                login_data, auth_required=False)
        
        if success:
            self.auth_token = data.get('access_token')
            self.current_user = data.get('user')
            
        self.log_result("authentication", "login", success,
                       f"Token received: {bool(self.auth_token)}" if success else None, error)
        
        if not self.auth_token:
            print("⚠️  No auth token available - subsequent tests may fail")
            return
            
        # 3. Test Get Current User
        success, data, error = self.make_request('GET', '/auth/me')
        self.log_result("authentication", "get_current_user", success,
                       f"User: {data.get('first_name')} {data.get('last_name')}" if success else None, error)
        
        # 4. Test Profile Update
        update_data = {
            "first_name": "Sarah Updated",
            "phone": "+65 9876 5432"
        }
        
        success, data, error = self.make_request('PUT', '/auth/me', update_data)
        self.log_result("authentication", "update_profile", success,
                       f"Updated name: {data.get('first_name')}" if success else None, error)
        
        # 5. Test Logout
        success, data, error = self.make_request('POST', '/auth/logout')
        self.log_result("authentication", "logout", success,
                       data.get('message') if success else None, error)

    def test_digital_id_api(self):
        """Test Digital ID endpoints"""
        print("\n🆔 Testing Digital ID API...")
        
        if not self.auth_token:
            self.log_result("digital_ids", "skipped", False, None, "No auth token available")
            return
            
        # 1. Get Digital ID (creates one if doesn't exist)
        success, data, error = self.make_request('GET', '/digital-ids/my-id')
        digital_id = data if success else None
        
        self.log_result("digital_ids", "get_my_id", success,
                       f"QR Code: {data.get('qr_code')[:20]}..." if success and data.get('qr_code') else None, error)
        
        # 2. Test Photo Upload (simulate with text file as image)
        test_image_content = b"fake_image_data_for_testing"
        files = {
            'file': ('test_photo.jpg', test_image_content, 'image/jpeg')
        }
        
        success, data, error = self.make_request('POST', '/digital-ids/upload-photo', 
                                                data={}, files=files)
        self.log_result("digital_ids", "upload_photo", success,
                       f"Status: {data.get('status')}" if success else None, error)

    def test_smart_pass_api(self):
        """Test Smart Pass endpoints"""
        print("\n🎫 Testing Smart Pass API...")
        
        if not self.auth_token:
            self.log_result("passes", "skipped", False, None, "No auth token available")
            return
            
        # 1. Get Locations
        success, data, error = self.make_request('GET', '/passes/locations')
        locations = data if success else []
        
        self.log_result("passes", "get_locations", success,
                       f"Found {len(locations)} locations" if success else None, error)
        
        if not locations:
            print("⚠️  No locations available - pass tests may fail")
            return
            
        # 2. Request a Pass
        pass_request = {
            "origin_location_id": locations[0].get('_id') if locations else "library",
            "destination_location_id": locations[1].get('_id') if len(locations) > 1 else "restroom",
            "time_limit_minutes": 15,
            "notes": "Need to use restroom"
        }
        
        success, data, error = self.make_request('POST', '/passes/request', pass_request)
        pass_id = data.get('_id') if success else None
        
        self.log_result("passes", "request_pass", success,
                       f"Pass ID: {pass_id}" if success else None, error)
        
        # 3. Get Active Pass
        success, data, error = self.make_request('GET', '/passes/active')
        self.log_result("passes", "get_active_pass", success,
                       f"Active pass: {data.get('_id')}" if success else None, error)
        
        # 4. End Pass (if we have one)
        if pass_id:
            success, data, error = self.make_request('POST', f'/passes/end/{pass_id}')
            self.log_result("passes", "end_pass", success,
                           f"Pass ended: {data.get('status')}" if success else None, error)

    def test_notifications_api(self):
        """Test Notifications endpoints"""
        print("\n📱 Testing Notifications API...")
        
        if not self.auth_token:
            self.log_result("notifications", "skipped", False, None, "No auth token available")
            return
            
        # Get My Notifications
        success, data, error = self.make_request('GET', '/notifications/my-notifications')
        notifications = data if success else []
        
        self.log_result("notifications", "get_my_notifications", success,
                       f"Found {len(notifications)} notifications" if success else None, error)

    def test_emergency_api(self):
        """Test Emergency endpoints"""
        print("\n🚨 Testing Emergency API...")
        
        if not self.auth_token:
            self.log_result("emergency", "skipped", False, None, "No auth token available")
            return
            
        # Check for Active Alert
        success, data, error = self.make_request('GET', '/emergency/active')
        self.log_result("emergency", "get_active_alert", success,
                       f"Active alert: {bool(data)}" if success else None, error)

    def test_invalid_scenarios(self):
        """Test invalid scenarios and error handling"""
        print("\n🚫 Testing Invalid Scenarios...")
        
        # Test invalid login
        invalid_login = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }
        
        success, data, error = self.make_request('POST', '/auth/login', 
                                                invalid_login, auth_required=False)
        # This should fail
        self.log_result("authentication", "invalid_login", not success,
                       "Correctly rejected invalid credentials" if not success else "Should have failed", 
                       error if not success else "Invalid login was accepted")
        
        # Test protected endpoint without auth
        old_token = self.auth_token
        self.auth_token = None
        
        success, data, error = self.make_request('GET', '/auth/me')
        # This should fail
        self.log_result("authentication", "no_auth_protection", not success,
                       "Correctly rejected unauthenticated request" if not success else "Should have failed",
                       error if not success else "Protected endpoint allowed access without auth")
        
        self.auth_token = old_token

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting AISJ Connect Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run test suites
        self.test_health_check()
        self.test_authentication_flow()
        self.test_digital_id_api()
        self.test_smart_pass_api()
        self.test_notifications_api()
        self.test_emergency_api()
        self.test_invalid_scenarios()
        
        end_time = time.time()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = self.test_results["summary"]["passed"] + self.test_results["summary"]["failed"]
        pass_rate = (self.test_results["summary"]["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {self.test_results['summary']['passed']}")
        print(f"❌ Failed: {self.test_results['summary']['failed']}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        print(f"⏱️  Duration: {end_time - start_time:.2f}s")
        
        if self.test_results["summary"]["errors"]:
            print("\n🔍 FAILED TESTS:")
            for error in self.test_results["summary"]["errors"]:
                print(f"   • {error}")
        
        # Save detailed results
        with open('/app/test_results_detailed.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
            
        print(f"\n📄 Detailed results saved to: /app/test_results_detailed.json")
        
        return self.test_results

if __name__ == "__main__":
    tester = AISJBackendTester()
    results = tester.run_all_tests()