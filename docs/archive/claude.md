# AISJ Connect - AI Coder Guide

## Overview

AISJ Connect is a full-stack school operations management platform designed for K-12 schools. It provides digital identity cards, smart hall passes, emergency communications, visitor management, and notification systems.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React Native 0.79 + Expo SDK 54 + TypeScript |
| **Backend** | Python FastAPI 0.110 |
| **Database** | MongoDB (Motor async driver) |
| **Auth** | JWT (24h access / 7d refresh tokens) |

## Project Structure

```
/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── core/           # Config, database, exceptions
│   │   ├── models/         # Pydantic data models
│   │   ├── repositories/   # Data access layer
│   │   └── services/       # Business logic
│   ├── routes/             # API endpoint handlers
│   ├── middleware/         # Security, rate limiting
│   ├── utils/              # Auth helpers, dependencies
│   └── server.py           # Main entry point
│
├── frontend/               # React Native (Expo) app
│   ├── app/               # Expo Router pages (file-based routing)
│   │   ├── (tabs)/        # Main tabbed navigation
│   │   ├── admin/         # Admin-only pages
│   │   ├── staff/         # Staff-only pages
│   │   └── visitor/       # Visitor pages
│   ├── api/               # API client modules
│   ├── components/        # Reusable UI components
│   └── contexts/          # React Context providers
```

## Quick Commands

### Backend
```bash
cd backend
pip install -r requirements.txt    # Install deps
uvicorn server:app --reload        # Start dev server (port 8000)
pytest                             # Run tests
black . && flake8 . && mypy .      # Format/lint/typecheck
```

### Frontend
```bash
cd frontend
yarn install                       # Install deps
npm start                          # Start Expo dev server
npm run android                    # Android emulator
npm run ios                        # iOS simulator
```

## API Base URL

- **Development**: `http://localhost:8000/api`
- **Health Check**: `GET /api/health`

## Core Features & File Locations

### 1. Authentication
- **Backend**: `backend/routes/auth.py`
- **Frontend**: `frontend/api/auth.ts`, `frontend/contexts/AuthContext.tsx`
- **Features**: Login, register, JWT tokens, profile management

### 2. Digital ID Cards
- **Backend**: `backend/routes/digital_ids.py`, `backend/app/models/digital_ids.py`
- **Frontend**: `frontend/app/(tabs)/id-card.tsx`, `frontend/api/digitalIds.ts`
- **Features**: ID creation, QR/barcode generation, photo upload, admin approval

### 3. Smart Pass System
- **Backend**: `backend/routes/passes.py`, `backend/routes/pass_advanced.py`
- **Frontend**: `frontend/app/(tabs)/smart-pass.tsx`, `frontend/api/passes.ts`
- **Features**: Hall pass requests, teacher approval, countdown timers, capacity limits

### 4. Emergency Communications
- **Backend**: `backend/routes/emergency.py`, `backend/routes/emergency_checkin.py`
- **Frontend**: `frontend/app/admin/emergency.tsx`, `frontend/api/emergency.ts`
- **Features**: Lockdown/fire/medical alerts, check-in system, real-time notifications

### 5. Visitor Management
- **Backend**: `backend/routes/visitors.py`, `backend/routes/visitor_enhanced.py`
- **Frontend**: `frontend/app/visitor/index.tsx`, `frontend/api/visitors.ts`
- **Features**: Check-in/out, badge generation, host notifications

### 6. Notifications
- **Backend**: `backend/routes/notifications.py`
- **Frontend**: `frontend/app/(tabs)/messages.tsx`, `frontend/api/notifications.ts`
- **Features**: Push notifications, announcements, role-based filtering

## User Roles

| Role | Access |
|------|--------|
| `STUDENT` | Basic features: ID, passes, messages |
| `PARENT` | View child info, notifications |
| `STAFF` | Approve passes, manage students |
| `ADMIN` | Full system access, all admin features |

## Key Patterns

### Backend
- **Dependency Injection**: Use `Depends()` for auth and database
- **Pydantic Models**: All request/response validation in `app/models/`
- **Async/Await**: Motor driver for non-blocking MongoDB operations
- **Config**: Environment settings in `app/core/config.py`

### Frontend
- **File-based Routing**: Pages in `app/` directory map to routes
- **Auth Context**: Global auth state via `contexts/AuthContext.tsx`
- **API Client**: Axios with auto token injection in `api/client.ts`
- **Tab Navigation**: Main screens in `app/(tabs)/`

## Database Collections

| Collection | Purpose |
|------------|---------|
| `users` | User accounts and profiles |
| `digital_ids` | ID card records |
| `passes` | Hall pass records |
| `emergency_alerts` | Emergency notifications |
| `visitors` | Visitor check-in logs |
| `notifications` | System notifications |

## Environment Variables

### Backend (`backend/.env`)
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=aisj_connect
SECRET_KEY=your-secret-key
ENVIRONMENT=development
```

## Testing

- **Backend**: `pytest` in `/backend` directory
- **Linting**: `black`, `flake8`, `isort`, `mypy`
- **Frontend**: `npm run lint` for ESLint

## Common Development Tasks

### Adding a New API Endpoint
1. Create/update model in `backend/app/models/`
2. Add route handler in `backend/routes/`
3. Register router in `backend/server.py`
4. Add frontend API function in `frontend/api/`

### Adding a New Screen
1. Create file in `frontend/app/` (route determined by filename)
2. For tabs: add to `frontend/app/(tabs)/`
3. For admin: add to `frontend/app/admin/`
4. Update navigation if needed in `_layout.tsx`

### Modifying Database Schema
1. Update Pydantic model in `backend/app/models/`
2. Add migration logic if needed in `backend/server.py` startup
3. Update TypeScript types in frontend

## Architecture Notes

- **Backend** follows a layered architecture: Routes → Services → Repositories → Database
- **Frontend** uses Expo Router's file-based routing with React Context for state
- **Auth flow**: Login → JWT stored in AsyncStorage → Axios interceptor adds to headers
- **Real-time**: Polling-based updates (no WebSocket currently)

## Important Files to Know

| File | Purpose |
|------|---------|
| `backend/server.py` | Backend entry point, router registration |
| `backend/app/core/config.py` | All backend configuration |
| `backend/app/core/database.py` | MongoDB connection manager |
| `frontend/app/_layout.tsx` | Root layout with Auth provider |
| `frontend/api/client.ts` | Axios instance with auth interceptors |
| `frontend/contexts/AuthContext.tsx` | Global authentication state |
