# AISJ Connect - Developer Guide 👩‍💻

> **Note:** This guide consolidates the previous `claude.md` and `VibeAI.md` documentation.

## 1. Overview

**AISJ Connect** (also known as CommElite/Swiss Army Knife) is a comprehensive school operations management platform designed for K-12 schools. It consolidates multiple disparate systems into a unified mobile application.

**Key Features:**
*   **Digital ID Cards**: Replace physical plastic IDs with dynamic digital versions.
*   **Smart Pass System**: Digital hall passes with timers and teacher approval workflows.
*   **Emergency Communications**: Instant alerts for lockdowns, fire drills, and medical emergencies.
*   **Visitor Management**: Streamlined check-in/out for campus visitors.
*   **Notifications**: Targeted push notifications and announcements.

## 2. Technology Stack 🛠️

### Frontend
*   **Framework**: React Native 0.79 + Expo SDK 54
*   **Routing**: Expo Router v5 (File-based routing)
*   **Language**: TypeScript
*   **State Management**: React Context + Hooks
*   **HTTP Client**: Axios
*   **UI/Styling**: Standard `StyleSheet`

### Backend
*   **Framework**: Python FastAPI 0.110
*   **Database**: MongoDB (via `motor` async driver)
*   **Authentication**: OAuth2 with Password Flow (JWT)
*   **Validation**: Pydantic v2
*   **Server**: Uvicorn

## 3. Project Structure 📂

```
/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── core/           # Config, database connection, exceptions
│   │   ├── models/         # Pydantic data models (Schemas)
│   │   ├── repositories/   # Data access layer (DAL)
│   │   └── services/       # Business logic layer
│   ├── routes/             # API endpoint handlers
│   ├── middleware/         # Custom middleware (CORS, Rate Limit)
│   ├── utils/              # Helper functions
│   └── server.py           # Main application entry point
│
├── frontend/               # React Native (Expo) app
│   ├── app/               # Expo Router pages (Screens)
│   │   ├── (tabs)/        # Main tab navigation layouts
│   │   ├── admin/         # Admin-specific routes
│   │   ├── staff/         # Staff-specific routes
│   │   ├── visitor/       # Visitor-specific routes
│   └── api/               # API client functions
│   ├── components/        # Reusable UI components
│   └── contexts/          # React Context providers (Auth, etc)
│
└── docs/                  # Project documentation
```

## 4. Quick Start 🚀

### Backend
1.  Navigate to `backend/`:
    ```bash
    cd backend
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Start development server:
    ```bash
    uvicorn server:app --reload
    ```
    *Server runs on `http://localhost:8000`*

### Frontend
1.  Navigate to `frontend/`:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start Expo server:
    ```bash
    npx expo start
    ```
    *Press `a` for Android, `i` for iOS simulator*

## 5. Architecture & Patterns 🏗️

### Backend: Clean Architecture
We follow a 3-layer architecture to decouple concerns:
1.  **Routes** (`backend/routes/`): Handle HTTP requests, parse input, call Services. **No business logic here.**
2.  **Services** (`backend/app/services/`): Contain business logic, validation, and orchestration.
3.  **Repositories** (`backend/app/repositories/`): Handle direct database interactions.

**Key Principals:**
*   **Dependency Injection**: Use FastAPI's `Depends` to inject Services into Routes, and Repositories into Services.
*   **Async/Await**: All I/O operations (DB, Network) must be async.

### Frontend: Expo Router
*   **Routing**: The directory structure in `frontend/app/` defines the navigation.
*   **API Layer**: Encapsulate all API calls in `frontend/api/`. Do not make fetch calls directly in components.
*   **Auth**: Managed globally via `AuthContext`.

## 6. Coding Conventions 📝

### General
*   **Type Safety**: Strict typing is enforced. Use Pydantic models for Backend and TypeScript Interfaces for Frontend.
*   **Documentation**: All new functions and classes must have docstrings/comments.

### AI Assistant Instructions 🤖
1.  **Context**: Always verify the current status in `ROADMAP.md` (now in `docs/ROADMAP.md`) before starting.
2.  **Files**: Update existing files whenever possible using `view_code_item` to understand context first.
3.  **Safety**: Never guess imports. Read the file first.
