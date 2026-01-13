# AISJ Swiss Army Knife Mobile Application
## Product Requirements Document & Development Roadmap

**Project Name:** AISJ Swiss Army Knife  
**App Name:** AISJ Connect  
**Version:** 1.0  
**Date:** December 2025  
**Platform:** iOS & Android (React Native via Expo)  
**Development Tool:** Emergent AI (Vibe Coding Platform)

---

## Executive Summary

The AISJ Swiss Army Knife is a comprehensive mobile application designed to consolidate essential school operations into a single, user-friendly platform. The app serves four distinct user groups: Staff, Students, Parents, and Administrators, providing tailored functionality for each role without integrating Student Information System (SIS) data. Core modules include Digital ID (ID123-style), Smart Pass (hall pass management), Emergency Communications, Push Notifications, and Visitor Management.

---

## Project Scope

### In Scope:
- ✅ Digital ID Cards with QR/barcode functionality
- ✅ Smart Pass system for student movement tracking
- ✅ Emergency communication system (lockdown, fire, evacuation)
- ✅ Push notification system for general communications
- ✅ Visitor management and check-in system
- ✅ Role-based access control (Staff, Student, Parent, Admin)

### Out of Scope:
- ❌ SIS integration (grades, attendance, schedules)
- ❌ Payment processing
- ❌ Learning Management System features
- ❌ Transportation tracking

---

## User Roles & Permissions

| Role      | User Type                      | Key Permissions                                                                     |
| :-------- | :----------------------------- | :---------------------------------------------------------------------------------- |
| **Student**   | Enrolled students              | View personal ID, create hall passes, receive notifications, check-in               |
| **Parent**    | Guardian/family members        | View child ID, receive notifications, visitor check-in, emergency alerts            |
| **Staff**     | Teachers, assistants           | Full ID, approve passes, hall monitor, create passes, notifications                 |
| **Admin**     | Super users, IT, Security      | All permissions, user management, emergency triggers, analytics                     |

---

## Feature Modules

### Module 1: Digital ID (ID123)

A secure digital identification system replacing physical ID cards with mobile credentials that can be scanned for verification and access control.

**Core Features:**
- Digital ID card with photo, name, role, grade/department
- QR code and barcode for scanning
- Offline access capability (cached credentials)
- Photo upload/selfie submission with admin approval
- Apple Wallet / Google Pay integration
- Remote deactivation by admin
- Expiration date management
- Fingerprint/Face ID authentication option

**User Stories:**
- As a student, I can display my ID on my phone for library access.
- As a staff member, I can scan student IDs to verify identity.
- As an admin, I can deactivate a lost device's ID remotely.

---

### Module 2: Smart Pass (Hall Pass System)

Digital hall pass management system that tracks student movement, provides accountability, and enhances safety by knowing student locations during class time.

**Core Features:**
- Digital pass creation with origin/destination
- Teacher approval workflow (optional per policy)
- Time limits with countdown and overtime alerts
- Hall Monitor view for security staff
- Maximum capacity per destination (bathroom limits)
- No-fly time restrictions
- Encounter prevention (block specific student meetups)
- Pass history and analytics reporting
- Missed class time tracking
- Kiosk mode for classroom devices

**User Stories:**
- As a student, I can request a pass to the bathroom without interrupting class.
- As a teacher, I can see how much class time a student has missed this week.
- As security, I can see all active passes in real-time on a hall monitor screen.

---

### Module 3: Emergency Communications

Critical alert system for campus emergencies including lockdowns, fire evacuations, and other safety situations. Designed for speed, reliability, and complete campus coverage.

**Alert Types:**
- **Lockdown:** Active threat. Shelter in place, lock doors, silence devices.
- **Fire/Evacuation:** Fire alarm, hazmat. Evacuate to designated assembly points.
- **Shelter in Place:** Weather, external threat. Move to safe interior location.
- **All Clear:** Emergency resolved. Resume normal operations.
- **Hold:** Hallway incident. Stay in current location, await instructions.

**Core Features:**
- One-tap emergency activation for authorized personnel
- Multi-channel delivery (push, SMS, email)
- Full-screen takeover alerts on devices
- Emergency attendance - account for all students
- Smart Pass integration - show all students currently in hallways
- Panic button functionality
- Follow-up messaging during active incidents
- All-clear notification with instructions
- Drill mode for practice scenarios

---

### Module 4: Push Notifications

General communication system for non-emergency announcements, reminders, and information sharing with targeted audience selection.

**Core Features:**
- Targeted messaging by role, grade, division
- Schedule notifications for future delivery
- Rich notifications with images and links
- In-app notification center/history
- Read receipts and delivery analytics
- Notification preferences per user
- Template library for common messages

---

### Module 5: Visitor Management

Comprehensive visitor check-in system to track all non-student/staff visitors on campus, verify identity, and maintain security records.

**Core Features:**
- Self-service kiosk check-in
- ID scanning (passport, Iqama, government ID)
- Photo capture at check-in
- Digital visitor badge generation (printable)
- Pre-registration for expected visitors
- Host notification upon visitor arrival
- Watchlist/banned person alerts
- Custody alert flags
- Check-out tracking
- Emergency evacuation visitor list
- Visitor history and reporting

---

## Technical Architecture

### Development Platform: Emergent AI

Emergent AI is a full-stack vibe-coding platform that enables rapid application development through natural language prompts. The platform handles frontend, backend, database, authentication, and deployment automatically.

**Platform Capabilities:**
- Full-stack web and mobile app generation
- React Native via Expo for mobile deployment
- Automatic database architecture and management
- Built-in authentication (email, OAuth)
- API integration capabilities
- Automatic testing and debugging
- One-click deployment
- GitHub integration for version control

### Tech Stack:
- **Frontend:** React Native (Expo)
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Authentication:** JWT with email/password + OAuth options
- **Push Notifications:** Firebase Cloud Messaging (FCM) + APNs
- **File Storage:** Base64 encoding (in MongoDB)
- **Hosting:** Emergent Cloud

---

## Database Architecture

### ✅ Collections Already Created:

All database collections are set up and ready. See `/app/backend/DATABASE_SCHEMA.md` for complete details.

**Core User Tables:**
- ✅ `users` - Primary user table (all authenticated users)
- ✅ `students` - Extended student information
- ✅ `staff` - Extended staff information
- ✅ `parent_student_relations` - Parent-child relationships

**Digital ID Tables:**
- ✅ `digital_ids` - Digital ID card records
- ✅ `id_scan_logs` - ID scan audit trail

**Smart Pass Tables:**
- ✅ `locations` - Campus locations (6 default locations seeded)
- ✅ `passes` - Hall pass records
- ✅ `encounter_groups` - Student separation rules
- ✅ `no_fly_times` - Time restrictions

**Emergency Tables:**
- ✅ `emergency_alerts` - Emergency notifications
- ✅ `emergency_check_ins` - User accountability

**Notification Tables:**
- ✅ `notifications` - Push notifications
- ✅ `notification_receipts` - Delivery tracking
- ✅ `notification_templates` - Reusable templates

**Visitor Tables:**
- ✅ `visitors` - Visitor information
- ✅ `visitor_logs` - Check-in/out records
- ✅ `visitor_pre_registrations` - Pre-registered visitors

**System Tables:**
- ✅ `audit_logs` - System audit trail
- ✅ `app_settings` - Configuration (5 default settings seeded)

---

## Implementation Roadmap

### ✅ Phase 0: Database Setup (COMPLETE)
- ✅ MongoDB database configured
- ✅ 20 collections created with indexes
- ✅ Seed data loaded
- ✅ Health check endpoints operational

### ✅ Phase 1: Foundation & Authentication (COMPLETE)
- ✅ JWT authentication system with 24-hour token expiration
- ✅ Login and registration screens with validation
- ✅ Role-based access control (student, parent, staff, admin)
- ✅ User management (CRUD) with admin console
- ✅ Core navigation with bottom tabs (5 tabs)
- ✅ Profile management with photo upload
- ✅ Rate limiting and account lockout protection
- ✅ Password strength validation

### ✅ Phase 2: Digital ID Module (COMPLETE)
- ✅ Digital ID card UI with flip animation
- ✅ QR code and barcode generation
- ✅ Photo upload and approval workflow
- ✅ ID scanning functionality with camera (staff/admin)
- ✅ Scan history and audit logging
- ✅ Biometric authentication option (Face ID/Touch ID)
- ✅ Admin ID management console (approve/reject/deactivate)
- ✅ Offline ID access (cached data)

### ✅ Phase 3: Smart Pass Module (COMPLETE)
- ✅ Location management (6 default locations seeded)
- ✅ Pass request workflow
- ✅ Teacher approval interface
- ✅ Hall monitor real-time view with WebSocket
- ✅ Pass timer and overtime alerts
- ✅ Encounter prevention logic
- ✅ No-fly time restrictions
- ✅ Location capacity management
- ✅ Pass analytics and reporting

### ✅ Phase 4: Emergency Communications (COMPLETE)
- ✅ Emergency alert triggers (admin only)
- ✅ 14 predefined alert templates by type (lockdown, fire, tornado, etc.)
- ✅ Multi-severity levels (info, low, medium, high, critical)
- ✅ Full-screen alert UI with emergency overlay
- ✅ Emergency check-in interface (safe/need help)
- ✅ Smart Pass integration (show students in hallways during emergency)
- ✅ Accountability report with student locations
- ✅ Drill mode support
- ✅ Reunification workflow

### ✅ Phase 5: Notifications & Visitor Management (COMPLETE)
- ✅ Push notification composer with rich UI
- ✅ Notification scheduling with date/time picker
- ✅ Target audience selection (all, students, parents, staff)
- ✅ Message templates library
- ✅ Sent/Scheduled tabs with management
- ✅ Visitor check-in/check-out workflow
- ✅ Visitor pre-registration
- ✅ Badge generation with QR codes
- ✅ Watchlist alerts
- ✅ Visitor analytics

### Phase 6: Testing & Launch
- [ ] User acceptance testing
- [ ] Security audit
- [ ] Performance optimization
- [ ] App Store / Play Store submission
- [ ] Staff training
- [ ] Phased rollout

---

## Design Guidelines

### Color Scheme:
- **Primary:** #1E3A5F (Professional Blue)
- **Secondary:** #2E5A8F (Lighter Blue)
- **Accent:** To be defined per module
- **Background:** #F5F7FA (Light Gray)
- **Text:** #1A1A1A (Dark Gray)
- **Success:** #10B981 (Green)
- **Warning:** #F59E0B (Orange)
- **Danger:** #EF4444 (Red)

### Navigation Structure:
Bottom tab navigation with 5 main sections:
1. **Home** - Dashboard with quick actions
2. **ID Card** - Digital ID display
3. **Smart Pass** - Pass management
4. **Messages** - Notifications center
5. **Profile** - User settings

### UI Principles:
- Clean, modern mobile-first design
- Large touch targets (minimum 44x44 points)
- Clear visual hierarchy
- Consistent spacing (8pt grid)
- Role-appropriate content
- Accessibility compliant

---

## Security & Compliance

### Data Privacy Requirements:
- All personal data encrypted at rest and in transit
- FERPA compliance for student data (US standard)
- Saudi PDPL compliance for local regulations
- Data retention policies by user type
- Right to access and deletion mechanisms

### Authentication Security:
- Password hashing with bcrypt (min 12 rounds)
- JWT tokens with 24-hour expiration
- Refresh token rotation
- Biometric authentication option (Face ID / Touch ID)
- Rate limiting on authentication endpoints

### API Security:
- All endpoints require authentication (except login/register)
- Role-based access control on all routes
- Input validation and sanitization
- MongoDB injection prevention
- HTTPS only communication

---

## Success Metrics

### Key Performance Indicators:
- **User Adoption:** 90% of students and staff onboarded within 30 days
- **Digital ID Usage:** 80% of ID verifications via app vs. physical cards
- **Pass Efficiency:** Average pass approval time < 30 seconds
- **Emergency Response:** Alert delivery to 100% of devices within 10 seconds
- **User Satisfaction:** App store rating > 4.5 stars

---

## Development Best Practices

### When Building with Emergent AI:

**Start with clear specifications:**
- Provide database schema upfront
- Describe user flows step-by-step
- Specify role-based permissions clearly
- Request specific UI components

**Iterate in small batches:**
- Build one feature at a time
- Test each feature before moving to next
- Use version control for major milestones

**Key Prompting Tips:**
- Be specific about data relationships
- Describe error handling requirements
- Specify loading states and edge cases
- Request mobile-optimized UI components

---

## Current Status

**Database:** ✅ COMPLETE (All 20 collections created and seeded)  
**Authentication:** 🔄 IN PROGRESS  
**Digital ID:** ⏳ PENDING  
**Smart Pass:** ⏳ PENDING  
**Emergency:** ⏳ PENDING  
**Notifications:** ⏳ PENDING  
**Visitor Management:** ⏳ PENDING  

---

**Next Steps:** Build JWT authentication system with login/registration screens and role-based navigation.

---

**— End of Roadmap —**
