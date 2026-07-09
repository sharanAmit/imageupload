# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trip Memories Platform — a self-hosted, private photo/video platform. Users create trips, invite collaborators, and upload media. Built with a FastAPI backend and a Vanilla JS SPA frontend.

## Commands

### Backend

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run dev server (from project root, NOT from backend/)
uvicorn backend.app.main:app --reload
# API: http://localhost:8000 | Swagger UI: http://localhost:8000/docs
```

### Frontend

```bash
# Serve frontend (Python built-in server)
python -m http.server -d frontend/ 8080
# Then open http://localhost:8080
```

> **Port mismatch**: The frontend `api.js` defaults `API_BASE_URL` to `http://localhost:8050`. If running uvicorn on the default port 8000, either start uvicorn on `--port 8050` or override the URL in `localStorage.setItem("api_base_url", "http://localhost:8000")` via browser console.

### Tests

```bash
# Run all tests (from project root)
pytest backend/tests/

# Run a single test file
pytest backend/tests/test_auth.py

# Run a single test function
pytest backend/tests/test_trips.py::test_trip_creation_and_membership
```

Tests use SQLite in-memory via `app.dependency_overrides[get_db]` — no PostgreSQL needed to run tests.

### Environment Setup

Copy `.env.example` to `.env` and fill in PostgreSQL credentials. The `DATABASE_URL` field is automatically rewritten from `postgresql://` to `postgresql+pg8000://` by `config.py` to avoid psycopg2 native compilation requirements.

## Architecture

### Backend (`backend/app/`)

Follows a layered architecture: **Routes → Services → Repositories → Models**.

| Layer | Location | Responsibility |
|---|---|---|
| Routes | `routes/` | HTTP controllers, request/response only |
| Services | `services/` | Business logic, orchestration |
| Repositories | `repositories/` | All database queries (SQLAlchemy ORM) |
| Schemas | `schemas/` | Pydantic request/response validation |
| Models | `models.py` | SQLAlchemy ORM table definitions |
| Config | `config.py` | Pydantic `Settings` loaded from `.env` |

**Database tables**: `users`, `trips`, `trip_members`, `media`, `activity_logs`, `trip_invites`. All public-facing records use a `uuid` column (string) as the external identifier; internal `id` (integer) is used only for FK joins.

**Auth**: JWT with separate access and refresh tokens via `python-jose`. `AuthService.get_current_user` is a FastAPI dependency used on protected routes. Also supports Google OAuth via `POST /auth/google` (requires `GOOGLE_CLIENT_ID` in `.env`). Direct `bcrypt` is used (not passlib) for Python 3.14+ compatibility.

**Media storage**: `StorageService` in `services/storage.py` is an ABC with `upload`, `delete`, `get_url`, and `get_file_path` methods. The active implementation is `LocalStorageService`, which stores files under `UPLOAD_DIR` (default: `uploads/` at project root) and serves them as static files at `/uploads/`. Storage keys follow the pattern `trips/{trip_uuid}/{photos|videos}/{uuid4}.{ext}`. See `docs/migration_guide.md` for switching to S3 — only the `get_storage_service()` factory needs to change.

**Roles**: `TripMember.role` can be `"owner"` or `"member"`. Owners can manage trips, members, and all media; members can upload and delete only their own media. Invites (`TripInvite`) are consumed on registration when an `invite_token` query param is passed to `POST /register`.

**Error handling**: A single `BaseHTTPMiddleware` in `middlewares/error_handler.py` catches `SQLAlchemyError` and unhandled exceptions globally. Route-level `HTTPException` is raised directly from services.

**Tables auto-created** on startup via `Base.metadata.create_all(bind=engine)` (skipped during pytest).

### Frontend (`frontend/`)

Vanilla JS ES-module SPA with hash-based routing. No build step required.

- `assets/js/api.js` — Central API client (`window.API`). Handles Bearer token injection, automatic silent token refresh on 401, and session cleanup on failed refresh.
- `assets/js/app.js` — `Router` class listening to `hashchange`. Dynamically `import()`s page modules from `assets/js/pages/` and calls their render function. Also owns the global search filter and toast/spinner utilities (`window.showToast`, `window.showSpinner`).
- `assets/js/pages/` — One module per route (`dashboard.js`, `trips.js`, `photos.js`, `profile.js`, `login_register.js`). Each exports named render functions called by the router.

Auth tokens are stored in `localStorage` (`access_token`, `refresh_token`, `user`). The `api_base_url` key in `localStorage` can override the backend URL at runtime (useful for pointing at different ports).
