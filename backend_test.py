#!/usr/bin/env python3
"""
AISJ Connect Backend API Testing Suite - COMPREHENSIVE ADMIN TESTING
Tests ALL backend endpoints including complete admin functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class AISJBackendTester:
    def __init__(self):
        # Use the production URL from frontend/.env
        self.base_url = "https://school-toolkit.preview.emergentagent.com/api"
        self.admin_token = None
        self.staff_token = None
        self.auth_token = None
        self.current_user = None
        self.test_results = {
            "authentication": {},
            "admin_dashboard": {},
            "admin_locations": {},
            "admin_ids": {},
            "admin_passes": {},
            "emergency_system": {},
            "digital_ids": {},
            "passes": {},
            "notifications": {},
            "emergency": {},
            "summary": {"passed": 0, "failed": 0, "errors": []}
        }
        
        # Admin credentials for comprehensive testing
        self.admin_user = {
            "email": "osama.chaudhry@gmail.com",
            "password": "Test12345"
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
        
        # Staff user for testing approval workflows
        self.staff_user = {
            "email": f"teacher_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com",
            "password": "Test12345",
            "first_name": "Teacher",
            "last_name": "Test",
            "role": "staff",
            "phone": "+1 555 0123"
        }
        
        # Track created resources for cleanup
        self.created_resources = {
            'locations': [],
            'users': [],
            'passes': [],
            'alerts': []
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
                    auth_required: bool = True, use_admin_token: bool = False, use_staff_token: bool = False) -> tuple[bool, Any, str]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        # Determine which token to use
        token = None
        if auth_required:
            if use_admin_token and self.admin_token:
                token = self.admin_token
            elif use_staff_token and self.staff_token:
                token = self.staff_token
            elif self.auth_token:
                token = self.auth_token
            elif self.admin_token:  # Fallback to admin token if available
                token = self.admin_token
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
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

    def test_admin_authentication(self):
        """Test admin login for comprehensive admin testing"""
        print("\n🔐 Testing Admin Authentication...")
        
        # Login as admin
        success, data, error = self.make_request('POST', '/auth/login', 
                                                self.admin_user, auth_required=False)
        
        if success:
            self.admin_token = data.get('access_token')
            
        self.log_result("authentication", "admin_login", success, 
                       f"Admin role: {data.get('user', {}).get('role')}" if success else None, error)
        
        return success

    def test_staff_user_creation(self):
        """Create and login staff user for approval workflow testing"""
        print("\n👨‍🏫 Creating Staff User for Testing...")
        
        # Register staff user
        success, data, error = self.make_request('POST', '/auth/register', 
                                                self.staff_user, auth_required=False)
        
        if success:
            self.created_resources['users'].append(self.staff_user['email'])
            
            # Login as staff
            login_data = {
                "email": self.staff_user["email"],
                "password": self.staff_user["password"]
            }
            
            success, data, error = self.make_request('POST', '/auth/login', 
                                                    login_data, auth_required=False)
            
            if success:
                self.staff_token = data.get('access_token')
                
        self.log_result("authentication", "staff_creation", success,
                       f"Staff user: {self.staff_user['email']}" if success else None, error)
        
        return success

    def test_admin_dashboard_stats(self):
        """Test admin dashboard statistics"""
        print("\n📊 Testing Admin Dashboard Stats...")
        
        if not self.admin_token:
            self.log_result("admin_dashboard", "skipped", False, None, "No admin token available")
            return
        
        # Get dashboard stats
        success, data, error = self.make_request('GET', '/admin/dashboard/stats', use_admin_token=True)
        if success:
            expected_fields = ['total_users', 'active_passes_count', 'pending_id_approvals', 'today_activity']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                details = f"Users: {data['total_users']}, Active passes: {data['active_passes_count']}"
                self.log_result("admin_dashboard", "dashboard_stats", True, details, None)
            else:
                self.log_result("admin_dashboard", "dashboard_stats", False, None, f"Missing fields: {missing_fields}")
        else:
            self.log_result("admin_dashboard", "dashboard_stats", False, None, error)
        
        # Get pass analytics
        success, data, error = self.make_request('GET', '/admin/analytics/passes', use_admin_token=True)
        if success:
            expected_fields = ['most_used_locations', 'average_duration_minutes', 'overtime_count']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                details = f"Avg duration: {data['average_duration_minutes']}min, Overtime: {data['overtime_count']}"
                self.log_result("admin_dashboard", "pass_analytics", True, details, None)
            else:
                self.log_result("admin_dashboard", "pass_analytics", False, None, f"Missing fields: {missing_fields}")
        else:
            self.log_result("admin_dashboard", "pass_analytics", False, None, error)
        
        # Get ID analytics
        success, data, error = self.make_request('GET', '/admin/analytics/ids', use_admin_token=True)
        if success:
            expected_fields = ['total_ids_issued', 'pending_approvals', 'rejected_photos']
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                details = f"Total IDs: {data['total_ids_issued']}, Pending: {data['pending_approvals']}"
                self.log_result("admin_dashboard", "id_analytics", True, details, None)
            else:
                self.log_result("admin_dashboard", "id_analytics", False, None, f"Missing fields: {missing_fields}")
        else:
            self.log_result("admin_dashboard", "id_analytics", False, None, error)

    def test_admin_location_management(self):
        """Test complete location CRUD operations"""
        print("\n🏢 Testing Admin Location Management...")
        
        if not self.admin_token:
            self.log_result("admin_locations", "skipped", False, None, "No admin token available")
            return
        
        # Get all locations
        success, data, error = self.make_request('GET', '/admin/locations/all?include_inactive=true', use_admin_token=True)
        if success:
            self.log_result("admin_locations", "get_all_locations", True, f"Found {len(data)} locations", None)
        else:
            self.log_result("admin_locations", "get_all_locations", False, None, error)
            return
        
        # Create new location
        test_location = {
            "name": f"Test Location {datetime.now().strftime('%H%M%S')}",
            "type": "classroom",
            "default_time_limit_minutes": 10,
            "requires_approval": True
        }
        
        success, data, error = self.make_request('POST', '/admin/locations', test_location, use_admin_token=True)
        if success and '_id' in data:
            location_id = data['_id']
            self.created_resources['locations'].append(location_id)
            self.log_result("admin_locations", "create_location", True, f"Created: {data['name']}", None)
            
            # Update location
            updated_data = {
                "name": f"Updated {test_location['name']}",
                "type": "classroom",
                "default_time_limit_minutes": 15,
                "requires_approval": False
            }
            
            success, data, error = self.make_request('PUT', f'/admin/locations/{location_id}', updated_data, use_admin_token=True)
            if success:
                self.log_result("admin_locations", "update_location", True, f"Updated to: {data['name']}", None)
                
                # Deactivate location
                success, data, error = self.make_request('DELETE', f'/admin/locations/{location_id}', use_admin_token=True)
                if success:
                    self.log_result("admin_locations", "deactivate_location", True, "Location deactivated", None)
                else:
                    self.log_result("admin_locations", "deactivate_location", False, None, error)
            else:
                self.log_result("admin_locations", "update_location", False, None, error)
        else:
            self.log_result("admin_locations", "create_location", False, None, error)

    def test_admin_id_management(self):
        """Test ID management endpoints"""
        print("\n🆔 Testing Admin ID Management...")
        
        if not self.admin_token:
            self.log_result("admin_ids", "skipped", False, None, "No admin token available")
            return
        
        # Get pending ID approvals
        success, data, error = self.make_request('GET', '/admin/ids/pending-approvals', use_admin_token=True)
        if success:
            self.log_result("admin_ids", "get_pending_approvals", True, f"Found {len(data)} pending approvals", None)
        else:
            self.log_result("admin_ids", "get_pending_approvals", False, None, error)
        
        # Get all IDs with filters
        success, data, error = self.make_request('GET', '/admin/ids/all?status=active', use_admin_token=True)
        if success:
            self.log_result("admin_ids", "get_all_ids", True, f"Found {len(data)} active IDs", None)
            
            # If we have IDs, test toggle status on first one
            if data and len(data) > 0:
                id_id = data[0]['_id']
                
                success, toggle_data, error = self.make_request('PUT', f'/admin/ids/{id_id}/toggle-status', use_admin_token=True)
                if success:
                    self.log_result("admin_ids", "toggle_id_status", True, f"Status toggled: {toggle_data.get('message')}", None)
                else:
                    self.log_result("admin_ids", "toggle_id_status", False, None, error)
        else:
            self.log_result("admin_ids", "get_all_ids", False, None, error)

    def test_pass_approval_workflow(self):
        """Test complete pass approval workflow with staff user"""
        print("\n📝 Testing Pass Approval Workflow...")
        
        if not self.staff_token:
            self.log_result("admin_passes", "skipped", False, None, "No staff token available")
            return
        
        # Get pending passes (staff token)
        success, data, error = self.make_request('GET', '/passes/teacher/pending', use_staff_token=True)
        if success:
            self.log_result("admin_passes", "get_pending_passes", True, f"Found {len(data)} pending passes", None)
            
            # If we have pending passes, test approval
            if data and len(data) > 0:
                pass_id = data[0]['_id']
                
                success, approve_data, error = self.make_request('POST', f'/passes/approve/{pass_id}', use_staff_token=True)
                if success:
                    self.log_result("admin_passes", "approve_pass", True, "Pass approved successfully", None)
                else:
                    self.log_result("admin_passes", "approve_pass", False, None, error)
        else:
            self.log_result("admin_passes", "get_pending_passes", False, None, error)
        
        # Get overtime passes
        success, data, error = self.make_request('GET', '/passes/overtime', use_staff_token=True)
        if success:
            self.log_result("admin_passes", "get_overtime_passes", True, f"Found {len(data)} overtime passes", None)
            
            # If we have overtime passes, test extension
            if data and len(data) > 0:
                pass_id = data[0]['_id']
                extend_data = {"additional_minutes": 5}
                
                success, extend_response, error = self.make_request('POST', f'/passes/extend/{pass_id}', extend_data, use_staff_token=True)
                if success:
                    self.log_result("admin_passes", "extend_pass", True, f"Pass extended: {extend_response.get('message')}", None)
                else:
                    self.log_result("admin_passes", "extend_pass", False, None, error)
        else:
            self.log_result("admin_passes", "get_overtime_passes", False, None, error)
        
        # Test bulk approve (with empty list)
        bulk_data = {"pass_ids": []}
        success, data, error = self.make_request('POST', '/passes/bulk-approve', bulk_data, use_staff_token=True)
        if success:
            self.log_result("admin_passes", "bulk_approve_passes", True, "Bulk approve endpoint working", None)
        else:
            self.log_result("admin_passes", "bulk_approve_passes", False, None, error)

    def test_emergency_system_comprehensive(self):
        """Test complete emergency system end-to-end"""
        print("\n🚨 Testing Emergency System Comprehensive...")
        
        if not self.admin_token:
            self.log_result("emergency_system", "skipped", False, None, "No admin token available")
            return
        
        # Check for active alert first
        success, data, error = self.make_request('GET', '/emergency/active', auth_required=False)
        if success:
            self.log_result("emergency_system", "get_active_alert", True, f"Active alert: {data is not None}", None)
        else:
            self.log_result("emergency_system", "get_active_alert", False, None, error)
        
        # Trigger emergency alert
        alert_data = {
            "alert_type": "lockdown",
            "severity": "high",
            "title": "Test Lockdown Alert",
            "message": "This is a comprehensive test lockdown alert for backend testing",
            "scope": "school_wide"
        }
        
        success, data, error = self.make_request('POST', '/emergency/trigger', alert_data, use_admin_token=True)
        alert_id = None
        if success and '_id' in data:
            alert_id = data['_id']
            self.created_resources['alerts'].append(alert_id)
            self.log_result("emergency_system", "trigger_alert", True, f"Alert created: {data['title']}", None)
            
            # Check in to emergency
            checkin_data = {
                "alert_id": alert_id,
                "status": "safe",
                "location": "Admin Office"
            }
            
            success, checkin_response, error = self.make_request('POST', '/emergency/check-in', checkin_data, use_admin_token=True)
            if success:
                self.log_result("emergency_system", "emergency_checkin", True, f"Checked in as: {checkin_response.get('status')}", None)
            else:
                self.log_result("emergency_system", "emergency_checkin", False, None, error)
            
            # Test reunification check-in
            reunion_data = {
                "alert_id": alert_id,
                "parent_name": "John Doe Test Parent",
                "station": "main"
            }
            
            success, reunion_response, error = self.make_request('POST', '/emergency/reunification/check-in', reunion_data, use_staff_token=bool(self.staff_token), use_admin_token=not bool(self.staff_token))
            if success:
                self.log_result("emergency_system", "reunification_checkin", True, f"Parent checked in: {reunion_response.get('parent_name')}", None)
            else:
                self.log_result("emergency_system", "reunification_checkin", False, None, error)
            
            # Get reunification status
            success, status_response, error = self.make_request('GET', f'/emergency/reunification/status/{alert_id}', use_staff_token=bool(self.staff_token), use_admin_token=not bool(self.staff_token))
            if success:
                details = f"Total students: {status_response.get('total_students')}, Checked-in parents: {status_response.get('checked_in_parents')}"
                self.log_result("emergency_system", "reunification_status", True, details, None)
            else:
                self.log_result("emergency_system", "reunification_status", False, None, error)
            
            # Resolve emergency
            success, resolve_response, error = self.make_request('POST', f'/emergency/resolve/{alert_id}', use_admin_token=True)
            if success:
                self.log_result("emergency_system", "resolve_emergency", True, "Emergency resolved successfully", None)
            else:
                self.log_result("emergency_system", "resolve_emergency", False, None, error)
        else:
            self.log_result("emergency_system", "trigger_alert", False, None, error)
        
        # Get emergency history
        success, data, error = self.make_request('GET', '/emergency/history', use_admin_token=True)
        if success:
            self.log_result("emergency_system", "get_emergency_history", True, f"Found {len(data)} historical alerts", None)
        else:
            self.log_result("emergency_system", "get_emergency_history", False, None, error)
        
        # Schedule a drill
        drill_data = {
            "drill_type": "fire",
            "scheduled_date": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "notes": "Monthly fire drill - backend test"
        }
        
        success, data, error = self.make_request('POST', '/emergency/drill/schedule', drill_data, use_admin_token=True)
        if success:
            self.log_result("emergency_system", "schedule_drill", True, f"Drill scheduled: {data.get('drill_type')}", None)
        else:
            self.log_result("emergency_system", "schedule_drill", False, None, error)
        
        # Get upcoming drills
        success, data, error = self.make_request('GET', '/emergency/drill/upcoming', use_staff_token=bool(self.staff_token), use_admin_token=not bool(self.staff_token))
        if success:
            self.log_result("emergency_system", "get_upcoming_drills", True, f"Found {len(data)} upcoming drills", None)
        else:
            self.log_result("emergency_system", "get_upcoming_drills", False, None, error)

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
        """Run all test suites including comprehensive admin testing"""
        print("🚀 Starting AISJ Connect Backend API Tests - COMPREHENSIVE ADMIN TESTING")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Phase 1: Basic Health and Authentication
        self.test_health_check()
        
        # Phase 2: Admin Authentication (Critical for admin tests)
        admin_auth_success = self.test_admin_authentication()
        
        # Phase 3: Staff User Creation (For approval workflows)
        staff_creation_success = self.test_staff_user_creation()
        
        # Phase 4: Comprehensive Admin Testing (Only if admin auth successful)
        if admin_auth_success:
            print("\n🔥 RUNNING COMPREHENSIVE ADMIN FEATURE TESTING...")
            self.test_admin_dashboard_stats()
            self.test_admin_location_management()
            self.test_admin_id_management()
            
            if staff_creation_success:
                self.test_pass_approval_workflow()
            
            self.test_emergency_system_comprehensive()
        else:
            print("⚠️  Skipping admin tests - admin authentication failed")
        
        # Phase 5: Regular User Testing
        self.test_authentication_flow()
        self.test_digital_id_api()
        self.test_smart_pass_api()
        self.test_notifications_api()
        self.test_emergency_api()
        self.test_invalid_scenarios()
        
        end_time = time.time()
        
        # Print comprehensive summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE BACKEND TEST SUMMARY - ADMIN FEATURES INCLUDED")
        print("=" * 80)
        
        total_tests = self.test_results["summary"]["passed"] + self.test_results["summary"]["failed"]
        pass_rate = (self.test_results["summary"]["passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {self.test_results['summary']['passed']}")
        print(f"❌ Failed: {self.test_results['summary']['failed']}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        print(f"⏱️  Duration: {end_time - start_time:.2f}s")
        
        # Category breakdown
        print(f"\n📋 CATEGORY BREAKDOWN:")
        categories = ['authentication', 'admin_dashboard', 'admin_locations', 'admin_ids', 
                     'admin_passes', 'emergency_system', 'digital_ids', 'passes', 'notifications', 'emergency']
        
        for category in categories:
            if category in self.test_results:
                category_tests = self.test_results[category]
                passed = sum(1 for test in category_tests.values() if test.get('success', False))
                total = len(category_tests)
                if total > 0:
                    print(f"   • {category.replace('_', ' ').title()}: {passed}/{total} ({passed/total*100:.0f}%)")
        
        if self.test_results["summary"]["errors"]:
            print(f"\n🔍 FAILED TESTS ({len(self.test_results['summary']['errors'])}):")
            for error in self.test_results["summary"]["errors"]:
                print(f"   • {error}")
        
        # Resource summary
        if any(self.created_resources.values()):
            print(f"\n🧹 TEST RESOURCES CREATED:")
            for resource_type, resources in self.created_resources.items():
                if resources:
                    print(f"   • {resource_type}: {len(resources)} items")
        
        # Overall assessment
        if pass_rate >= 90:
            assessment = "🎉 EXCELLENT - All major admin features working"
        elif pass_rate >= 75:
            assessment = "✅ GOOD - Most admin features working, minor issues"
        elif pass_rate >= 50:
            assessment = "⚠️  NEEDS ATTENTION - Some admin features failing"
        else:
            assessment = "❌ CRITICAL ISSUES - Major admin functionality broken"
        
        print(f"\n🎯 OVERALL ASSESSMENT: {assessment}")
        
        # Save detailed results
        with open('/app/test_results_detailed.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
            
        print(f"\n📄 Detailed results saved to: /app/test_results_detailed.json")
        
        return self.test_results

if __name__ == "__main__":
    tester = AISJBackendTester()
    results = tester.run_all_tests()