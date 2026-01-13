# VibeAI.md - AISJ Connect Codebase Guide

This document provides a comprehensive overview of the AISJ Connect (CommElite) codebase, designed to assist AI agents and developers in understanding the project structure, workflows, and conventions.

## 1. Project Overview

**App Name:** AISJ Connect  
**Description:** A comprehensive mobile application for school operations, including Digital ID, Smart Pass, Emergency Communications, and Visitor Management.  
**Platform:** Mobile (iOS & Android) via React Native (Expo).  
**Backend:** Python FastAPI with MongoDB.

## 2. Technology Stack

### Frontend
-   **Framework:** React Native (Expo SDK 54)
-   **Routing:** Expo Router v5 (File-based routing)
-   **Language:** TypeScript
-   **HTTP Client:** Axios
-   **State Management:** React Context / Hooks
-   **Styling:** React Native `StyleSheet` (Standard)
-   **Icons:** `@expo/vector-icons`

### Backend
-   **Framework:** FastAPI
-   **Language:** Python 3.x
-   **Database:** MongoDB (via `motor` async driver)
-   **Validation:** Pydantic v2
-   **Authentication:** PyJWT (OAuth2 with Password Flow)
-   **Server:** Uvicorn

## 3. Codebase Structure

### Root Directory
-   `backend/`: Python FastAPI server code.
-   `frontend/`: Expo React Native app code.
-   `ROADMAP.md`: Project status and product requirements.
-   `VibeAI.md`: This guide.

### Backend Structure (`backend/`)
-   `app/`: Main application source code.
    -   `core/`: Configuration and core utilities.
    -   `models/`: Pydantic data models.
    -   `routers/`: API route handlers.
    -   `services/`: Business logic services.
-   `tests/`: Backend tests.
-   `server.py`: Application entry point (legacy wrapper).
-   `database.py`: MongoDB connection logic (legacy wrapper).
-   `requirements.txt`: Python dependencies.

### Frontend Structure (`frontend/`)
-   `app/`: Expo Router pages and layouts.
    -   `(tabs)/`: Main tab navigation.
    -   `_layout.tsx`: Root layout.
    -   `index.tsx`: Entry screen.
-   `api/`: Centralized API client and modules.
-   `components/`: Reusable UI components.
-   `contexts/`: React Context providers.
-   `assets/`: Static assets (images, fonts).
-   `package.json`: JS dependencies and scripts.

## 4. Development Workflows

### Backend
1.  **Setup:** Create virtual env, install `requirements.txt`.
2.  **Run:** `uvicorn server:app --reload` (or run `server.py` directly if configured).
3.  **Linting:** Uses `black`, `flake8`, `isort`.

### Frontend
1.  **Setup:** `npm install` or `yarn install`.
2.  **Run:** `npx expo start` (or `npm start`).
3.  **Linting:** `eslint`.

## 5. Coding Conventions

### General
-   **AI Interaction:** Always check `ROADMAP.md` for the current task status before starting work. Update it when tasks are completed.
-   **Type Safety:** Strict typing is enforced. Use TypeScript interfaces/types for frontend and Pydantic models for backend.

### Frontend (React Native)
-   **Components:** Functional components with Hooks.
-   **Navigation:** Use `expo-router` conventions (`useRouter`, `Link`, file-based structure).
-   **Styling:** Use `StyleSheet.create` for styles. Avoid inline styles for complex elements.
-   **Async:** Use `async/await` for API calls.

### Backend (FastAPI)
-   **Async:** Use `async def` for route handlers and DB operations.
-   **Models:** Define Pydantic models for all Request/Response bodies.
-   **Routes:** Use `APIRouter` to modularize endpoints.
-   **DB:** Use `motor` for non-blocking MongoDB operations.

## 6. AI Assistant Instructions

1.  **Context Awareness:** Before making changes, read `ROADMAP.md` to understand the bigger picture.
2.  **File Creation:** When creating new files, ensure they are properly linked (e.g., new routes added to `server.py`, new pages added to navigation).
3.  **Error Handling:** Implement robust error handling in both frontend (user feedback) and backend (HTTP error codes).
4.  **Documentation:** Add docstrings to Python functions and comments to complex JS logic.
5.  **Verification:** After implementing a feature, verify it against the requirements in `ROADMAP.md`.
