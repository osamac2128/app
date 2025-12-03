# AISJ Swiss Army Knife - MongoDB Database Schema

## Overview
This document describes the MongoDB database structure for the AISJ Swiss Army Knife mobile application. The database has been converted from the original PostgreSQL schema to MongoDB format.

## Database Name
`test_database`

## Collections Summary

### Core User Collections
1. **users** - Main user accounts (students, parents, staff, admin)
2. **students** - Student-specific data and settings
3. **staff** - Staff-specific data and permissions
4. **parent_student_relations** - Relationships between parents and students

### Digital ID System
5. **digital_ids** - QR codes and barcodes for user identification
6. **id_scan_logs** - Audit trail of ID scans

### Smart Pass System
7. **locations** - Campus locations (classrooms, bathrooms, offices, etc.)
8. **passes** - Hall pass requests and tracking
9. **encounter_groups** - Student separation rules
10. **no_fly_times** - Time-based pass restrictions

### Emergency Communication
11. **emergency_alerts** - Emergency notifications and drills
12. **emergency_check_ins** - Accountability tracking during emergencies

### Notification System
13. **notifications** - Push notifications and announcements
14. **notification_receipts** - Delivery tracking per user
15. **notification_templates** - Reusable notification templates

### Visitor Management
16. **visitors** - Visitor information and watchlist
17. **visitor_logs** - Check-in/check-out records
18. **visitor_pre_registrations** - Pre-registered visitor appointments

### System Collections
19. **audit_logs** - System-wide audit trail
20. **app_settings** - Application configuration

---

## Detailed Collection Schemas

### 1. users
Main user collection for all user types (student, parent, staff, admin).

**Fields:**
- `_id`: ObjectId (auto-generated)
- `email`: String (unique, required)
- `password_hash`: String (required)
- `first_name`: String (required)
- `last_name`: String (required)
- `role`: Enum ['student', 'parent', 'staff', 'admin'] (required)
- `phone`: String (optional)
- `profile_photo_url`: String (optional, base64 or URL)
- `status`: Enum ['active', 'inactive', 'suspended'] (default: 'active')
- `device_tokens`: Array of Strings (for push notifications)
- `notification_preferences`: Object (JSON preferences)
- `last_login_at`: DateTime (optional)
- `created_at`: DateTime (auto-generated)
- `updated_at`: DateTime (auto-updated)

**Indexes:**
- email (unique)
- role
- status

---

### 2. students
Extended information for users with role='student'.

**Fields:**
- `_id`: ObjectId (auto-generated)
- `user_id`: String (reference to users._id, required)
- `student_id`: String (unique student identifier, required)
- `grade`: String (e.g., "9", "10", required)
- `division`: Enum ['ES', 'MS', 'HS'] (required)
- `homeroom`: String (optional)
- `advisor_id`: String (reference to users._id, optional)
- `daily_pass_limit`: Integer (default: 5)
- `pass_time_limit_minutes`: Integer (default: 5)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- user_id
- student_id (unique)
- grade
- division

---

### 3. staff
Extended information for users with role='staff'.

**Fields:**
- `_id`: ObjectId
- `user_id`: String (reference to users._id, required)
- `employee_id`: String (unique, required)
- `department`: String (optional)
- `position`: String (optional)
- `room_number`: String (optional)
- `can_approve_passes`: Boolean (default: true)
- `is_hall_monitor`: Boolean (default: false)
- `can_trigger_emergency`: Boolean (default: false)
- `can_manage_visitors`: Boolean (default: false)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- user_id
- employee_id (unique)

---

### 4. parent_student_relations
Many-to-many relationship between parents and students.

**Fields:**
- `_id`: ObjectId
- `parent_user_id`: String (reference to users._id, required)
- `student_id`: String (reference to students._id, required)
- `relationship`: Enum ['mother', 'father', 'guardian', 'other'] (required)
- `is_primary`: Boolean (default: false)
- `can_pickup`: Boolean (default: true)
- `can_receive_alerts`: Boolean (default: true)
- `created_at`: DateTime

**Indexes:**
- parent_user_id
- student_id
- parent_user_id + student_id (unique compound)

---

### 5. digital_ids
Digital ID cards with QR codes and barcodes.

**Fields:**
- `_id`: ObjectId
- `user_id`: String (reference to users._id, required, unique)
- `qr_code`: String (unique, required)
- `barcode`: String (unique, required)
- `photo_url`: String (optional, base64 or URL)
- `photo_status`: Enum ['pending', 'approved', 'rejected'] (default: 'pending')
- `submitted_photo_url`: String (optional)
- `photo_reviewed_by`: String (reference to users._id, optional)
- `photo_reviewed_at`: DateTime (optional)
- `is_active`: Boolean (default: true)
- `issued_at`: DateTime
- `expires_at`: DateTime (optional)
- `deactivated_at`: DateTime (optional)
- `deactivated_by`: String (optional)
- `deactivation_reason`: String (optional)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- user_id (unique)
- qr_code (unique)
- barcode (unique)
- is_active

---

### 6. id_scan_logs
Audit trail of all ID scans.

**Fields:**
- `_id`: ObjectId
- `digital_id_id`: String (reference to digital_ids._id, required)
- `scanned_by`: String (reference to users._id, optional)
- `location`: String (optional)
- `purpose`: Enum ['entry', 'exit', 'verification', 'lunch', 'event'] (optional)
- `device_info`: String (optional)
- `scan_result`: String (default: 'success')
- `scanned_at`: DateTime

**Indexes:**
- digital_id_id
- scanned_at (descending)

---

### 7. locations
Campus locations where students can request passes to.

**Fields:**
- `_id`: ObjectId
- `name`: String (required)
- `building`: String (optional)
- `floor`: String (optional)
- `room_number`: String (optional)
- `type`: Enum ['classroom', 'bathroom', 'office', 'library', 'gym', 'cafeteria', 'nurse', 'counselor', 'other'] (required)
- `max_capacity`: Integer (optional)
- `requires_approval`: Boolean (default: false)
- `default_time_limit_minutes`: Integer (default: 5)
- `is_active`: Boolean (default: true)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- type
- building
- is_active

**Seed Data:** 6 default locations (Main Office, Library, Gymnasium, Cafeteria, Nurse's Office, Counselor's Office)

---

### 8. passes
Hall pass requests and tracking.

**Fields:**
- `_id`: ObjectId
- `student_id`: String (reference to students._id, required)
- `origin_location_id`: String (reference to locations._id, required)
- `destination_location_id`: String (reference to locations._id, required)
- `status`: Enum ['pending', 'approved', 'active', 'completed', 'expired', 'cancelled'] (default: 'pending')
- `requested_at`: DateTime
- `approved_at`: DateTime (optional)
- `approved_by`: String (reference to users._id, optional)
- `departed_at`: DateTime (optional)
- `arrived_at`: DateTime (optional)
- `returned_at`: DateTime (optional)
- `time_limit_minutes`: Integer (default: 5)
- `is_overtime`: Boolean (default: false)
- `overtime_notified_at`: DateTime (optional)
- `notes`: String (optional)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- student_id
- status
- requested_at (descending)
- origin_location_id
- destination_location_id

---

### 9. encounter_groups
Groups of students who should not have passes at the same time.

**Fields:**
- `_id`: ObjectId
- `name`: String (optional)
- `student_ids`: Array of Strings (references to students._id, required)
- `created_by`: String (reference to users._id, required)
- `reason`: String (optional)
- `is_active`: Boolean (default: true)
- `expires_at`: DateTime (optional)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- is_active

---

### 10. no_fly_times
Time periods when passes cannot be issued.

**Fields:**
- `_id`: ObjectId
- `name`: String (required)
- `start_time`: String (format: "HH:MM:SS")
- `end_time`: String (format: "HH:MM:SS")
- `days_of_week`: Array of Integers (1=Monday, 7=Sunday, default: [1,2,3,4,5])
- `affected_divisions`: Array of Enum ['ES', 'MS', 'HS'] (optional)
- `affected_grades`: Array of Strings (optional)
- `is_active`: Boolean (default: true)
- `created_at`: DateTime

---

### 11. emergency_alerts
Emergency notifications sent to users.

**Fields:**
- `_id`: ObjectId
- `type`: Enum ['lockdown', 'fire', 'shelter', 'hold', 'all_clear', 'drill', 'medical', 'weather'] (required)
- `title`: String (required)
- `message`: String (required)
- `severity`: Enum ['critical', 'high', 'medium', 'low'] (required)
- `instructions`: String (optional)
- `is_drill`: Boolean (default: false)
- `triggered_by`: String (reference to users._id, required)
- `triggered_at`: DateTime
- `resolved_at`: DateTime (optional)
- `resolved_by`: String (reference to users._id, optional)
- `resolution_notes`: String (optional)
- `affected_buildings`: Array of Strings (optional)
- `affected_divisions`: Array of Enum (optional)
- `parent_alert_id`: String (reference to emergency_alerts._id, optional)
- `created_at`: DateTime

**Indexes:**
- type
- triggered_at (descending)
- resolved_at (for active alerts)

---

### 12. emergency_check_ins
User accountability tracking during emergencies.

**Fields:**
- `_id`: ObjectId
- `alert_id`: String (reference to emergency_alerts._id, required)
- `user_id`: String (reference to users._id, required)
- `status`: Enum ['safe', 'need_help', 'unaccounted'] (default: 'unaccounted')
- `location`: String (optional)
- `checked_in_at`: DateTime (optional)
- `checked_by`: String (reference to users._id, optional)
- `notes`: String (optional)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- alert_id
- user_id
- status
- alert_id + user_id (unique compound)

---

### 13. notifications
Push notifications and announcements.

**Fields:**
- `_id`: ObjectId
- `title`: String (required)
- `body`: String (required)
- `type`: Enum ['general', 'announcement', 'reminder', 'event', 'urgent'] (default: 'general')
- `image_url`: String (optional, base64 or URL)
- `action_url`: String (optional)
- `target_roles`: Array of Enum (optional)
- `target_grades`: Array of Strings (optional)
- `target_divisions`: Array of Enum (optional)
- `target_user_ids`: Array of Strings (optional)
- `created_by`: String (reference to users._id, required)
- `scheduled_at`: DateTime (optional)
- `sent_at`: DateTime (optional)
- `status`: Enum ['draft', 'scheduled', 'sent', 'cancelled'] (default: 'draft')
- `total_recipients`: Integer (default: 0)
- `delivered_count`: Integer (default: 0)
- `read_count`: Integer (default: 0)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- status
- scheduled_at
- created_at (descending)

---

### 14. notification_receipts
Tracking of notification delivery to individual users.

**Fields:**
- `_id`: ObjectId
- `notification_id`: String (reference to notifications._id, required)
- `user_id`: String (reference to users._id, required)
- `delivered_at`: DateTime (optional)
- `read_at`: DateTime (optional)
- `delivery_status`: Enum ['pending', 'delivered', 'failed'] (default: 'pending')
- `error_message`: String (optional)
- `created_at`: DateTime

**Indexes:**
- notification_id
- user_id
- delivery_status
- notification_id + user_id (unique compound)

---

### 15. notification_templates
Reusable notification templates.

**Fields:**
- `_id`: ObjectId
- `name`: String (required)
- `title_template`: String (required)
- `body_template`: String (required)
- `type`: Enum (required)
- `created_by`: String (reference to users._id, optional)
- `is_active`: Boolean (default: true)
- `created_at`: DateTime

---

### 16. visitors
Visitor information and watchlist.

**Fields:**
- `_id`: ObjectId
- `first_name`: String (required)
- `last_name`: String (required)
- `email`: String (email format, optional)
- `phone`: String (optional)
- `id_type`: Enum ['passport', 'iqama', 'national_id', 'drivers_license', 'other'] (optional)
- `id_number`: String (optional)
- `id_document_url`: String (optional, base64 or URL)
- `photo_url`: String (optional, base64 or URL)
- `company`: String (optional)
- `is_on_watchlist`: Boolean (default: false)
- `watchlist_reason`: String (optional)
- `watchlist_added_by`: String (reference to users._id, optional)
- `watchlist_added_at`: DateTime (optional)
- `notes`: String (optional)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- last_name + first_name (compound)
- id_number
- is_on_watchlist

---

### 17. visitor_logs
Visitor check-in and check-out records.

**Fields:**
- `_id`: ObjectId
- `visitor_id`: String (reference to visitors._id, required)
- `purpose`: Enum ['meeting', 'delivery', 'contractor', 'parent', 'event', 'interview', 'other'] (required)
- `purpose_detail`: String (optional)
- `host_user_id`: String (reference to users._id, optional)
- `host_notified_at`: DateTime (optional)
- `badge_number`: String (optional)
- `checked_in_at`: DateTime (auto-generated)
- `checked_out_at`: DateTime (optional)
- `checked_in_by`: String (reference to users._id, optional)
- `checked_out_by`: String (reference to users._id, optional)
- `destination`: String (optional)
- `is_pre_registered`: Boolean (default: false)
- `pre_registration_id`: String (optional)
- `notes`: String (optional)
- `created_at`: DateTime

**Indexes:**
- visitor_id
- checked_in_at (descending)
- checked_out_at (for active visits)
- host_user_id

---

### 18. visitor_pre_registrations
Pre-registered visitor appointments.

**Fields:**
- `_id`: ObjectId
- `visitor_email`: String (email format, optional)
- `visitor_first_name`: String (required)
- `visitor_last_name`: String (required)
- `visitor_phone`: String (optional)
- `visitor_company`: String (optional)
- `purpose`: Enum (required)
- `purpose_detail`: String (optional)
- `host_user_id`: String (reference to users._id, required)
- `expected_date`: String (ISO date format)
- `expected_time`: String (format: "HH:MM:SS", optional)
- `access_code`: String (unique, optional)
- `is_used`: Boolean (default: false)
- `used_at`: DateTime (optional)
- `created_by`: String (reference to users._id, required)
- `created_at`: DateTime

**Indexes:**
- expected_date
- access_code (unique, sparse)

---

### 19. audit_logs
System-wide audit trail for all important actions.

**Fields:**
- `_id`: ObjectId
- `user_id`: String (reference to users._id, optional)
- `action`: String (e.g., 'create', 'update', 'delete', 'login', required)
- `entity_type`: String (e.g., 'user', 'pass', 'visitor', required)
- `entity_id`: String (optional)
- `old_values`: Object (JSON, optional)
- `new_values`: Object (JSON, optional)
- `ip_address`: String (optional)
- `user_agent`: String (optional)
- `created_at`: DateTime

**Indexes:**
- user_id
- action
- entity_type + entity_id (compound)
- created_at (descending)

---

### 20. app_settings
Application configuration and settings.

**Fields:**
- `_id`: ObjectId
- `key`: String (unique, required)
- `value`: Any (JSON-compatible, required)
- `description`: String (optional)
- `updated_by`: String (reference to users._id, optional)
- `created_at`: DateTime
- `updated_at`: DateTime

**Indexes:**
- key (unique)

**Seed Data:**
- `default_pass_time_limit`: 5 (Default pass duration in minutes)
- `max_daily_passes`: 5 (Maximum passes per student per day)
- `enable_encounter_prevention`: true (Enable encounter prevention feature)
- `emergency_sms_enabled`: true (Send SMS for emergency alerts)
- `visitor_badge_required`: true (Require visitor badges)

---

## Data Relationships

### User Hierarchy
```
users (parent collection)
├── students (user_id → users._id)
├── staff (user_id → users._id)
└── parent_student_relations (parent_user_id → users._id)
```

### Digital ID System
```
users
└── digital_ids (user_id → users._id)
    └── id_scan_logs (digital_id_id → digital_ids._id)
```

### Pass System
```
students
└── passes (student_id → students._id)
    ├── origin_location_id → locations._id
    └── destination_location_id → locations._id
```

### Emergency System
```
emergency_alerts
└── emergency_check_ins (alert_id → emergency_alerts._id, user_id → users._id)
```

### Notification System
```
notifications
└── notification_receipts (notification_id → notifications._id, user_id → users._id)
```

### Visitor System
```
visitors
└── visitor_logs (visitor_id → visitors._id)
    └── visitor_pre_registrations (pre_registration_id → visitor_pre_registrations._id)
```

---

## Notes

1. **ObjectId vs String IDs**: MongoDB uses ObjectId by default, but references are stored as strings for flexibility.

2. **Images**: All image fields (`profile_photo_url`, `photo_url`, etc.) can store either:
   - Base64-encoded image data (recommended for mobile apps)
   - External URLs

3. **Enums**: All enum values are stored as strings in MongoDB and validated at the application level via Pydantic models.

4. **Timestamps**: All timestamps use Python's `datetime.utcnow()` for consistency.

5. **Indexes**: Compound indexes and unique constraints are created automatically on application startup.

6. **Soft Deletes**: The schema supports soft deletes via status fields (e.g., `is_active`, `status`).

7. **Audit Trail**: The `audit_logs` collection can track all important actions across the application.

---

## API Endpoints Status

Currently, only basic health check endpoints are available:
- `GET /api/` - API info
- `GET /api/health` - Database health check

All CRUD endpoints for each module will be implemented as per your sequential instructions.
