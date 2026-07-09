# Trip Memories Platform 📸

A production-quality, completely private, self-hosted Travel Memories Platform similar to Google Photos. Save, organize, share, and relive your trip photos and videos in a secure sandbox hosted entirely on your own infrastructure.

Built with a modular **Python FastAPI** backend (SQLAlchemy, Repository Pattern) and a premium, ultra-clean, minimal **Vanilla JavaScript & Bootstrap 5** single-page application (SPA) styled with Apple/Notion design principles.

---

## Key Features

- **Private Auth**: Secure signup, login, JWT token issue, and token refresh.
- **Collaborative Trips**: Create trips and invite other users as co-owners or standard members.
- **Responsive Masonry Gallery**: Pinterest-like column layout with lazy loading.
- **Lightbox Preview Panel**: Zoom and inspect photo metadata or stream video memories instantly.
- **Secure Access Control**:
  - **Trip Owners** can edit/delete trips, manage members, and delete any media.
  - **Members** can upload photos/videos, view galleries, download files, and delete their own uploads.
- **Activity Timeline**: Global and trip-level user audit logs.
- **Future AWS Compatibility**: Ready to migrate from local storage to Amazon S3 + CloudFront without altering route handlers or frontend scripts.

---

## Folder Structure

```text
trip-memory/
├── backend/
│   └── app/
│       ├── config.py           # Configuration & environment loader
│       ├── database.py         # SQLAlchemy Engine & Session provider
│       ├── main.py             # FastAPI App & router registry
│       ├── models.py           # Database models (User, Trip, Member, Media, Activity)
│       ├── middlewares/
│       │   └── error_handler.py# Global exception handling & logging interceptors
│       ├── repositories/       # Isolated DB database transaction layers
│       │   ├── user_repository.py
│       │   ├── trip_repository.py
│       │   ├── media_repository.py
│       │   └── activity_repository.py
│       ├── routes/             # REST Route controllers
│       │   ├── auth.py
│       │   ├── trips.py
│       │   ├── media.py
│       │   └── activities.py
│       ├── schemas/            # Pydantic request/response serializers
│       │   ├── user.py
│       │   ├── trip.py
│       │   ├── media.py
│       │   └── activity.py
│       └── services/           # Core Business services & storage implementations
│           ├── auth_service.py
│           ├── trip_service.py
│           ├── media_service.py
│           ├── activity_service.py
│           └── storage.py      # Abstract storage interface & LocalStorage
├── docs/
│   └── migration_guide.md      # AWS S3 + CloudFront transition instructions
├── frontend/                   # Vanilla JavaScript SPA Client
│   ├── assets/
│   │   ├── css/
│   │   │   └── style.css       # Core typography, dark mode tokens, masonry, transitions
│   │   └── js/
│   │       ├── api.js          # API client with token automatic-refresh interceptor
│   │       ├── app.js          # SPA router and Toast alert utilities
│   │       └── pages/          # Render modules (dashboard, login/register, trips, profile)
│   └── index.html              # Main single page application landing shell
├── uploads/                    # Local server storage location (created automatically)
├── requirements.txt            # Python environment packages
├── .env.example                # Config template environment variables
└── README.md                   # Project documentation
```

---

## Installation & Setup

### Prerequisites
- Python 3.9+
- PostgreSQL database running locally or on RDS.

### Step 1: Clone and Configure Environment
1. Clone this repository to your workspace.
2. Duplicate `.env.example` as `.env`:
   ```bash
   copy .env.example .env
   ```
3. Update `.env` with your PostgreSQL database credentials and preferred JWT secret keys:
   ```env
   DATABASE_URL=postgresql://your_user:your_password@localhost:5432/your_database
   ```

### Step 2: Set Up Python Backend
1. Initialize a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
2. Install the required python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the FastAPI development server:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
   The backend API will start on **`http://localhost:8000`** with interactive Swagger documentation available at `http://localhost:8000/docs`.
   *Note: Database tables are automatically initialized on application startup.*

### Step 3: Run the Frontend Client
Serve the `frontend/` directory using any web server. For local development:
- **Python server (recommended)**:
  ```bash
  python -m http.server -d frontend/ 8080
  ```
- **VSCode Live Server**: Open `frontend/index.html` and click "Go Live" (runs on port `5500`).

Open your browser and navigate to the local frontend address (e.g. `http://localhost:8080`).

---

## REST API Summary

### Authentication
- `POST /register`: Register user credentials.
- `POST /login`: Log in to retrieve JWT access & refresh tokens.
- `POST /refresh`: Refresh expired access tokens securely.
- `GET /me`: Fetch authenticated user profile details.
- `POST /change-password`: Update profile password.
- `POST /logout`: Logout session.

### Trips
- `POST /trip`: Create a trip (creator becomes Owner).
- `GET /trip`: List all trips current user has access to.
- `GET /trip/{uuid}`: Fetch detailed trip layout and members list.
- `PUT /trip/{uuid}`: Edit trip name and description (Owner only).
- `DELETE /trip/{uuid}`: Remove trip and delete all stored media (Owner only).

### Members
- `POST /trip/{uuid}/invite`: Invite user by email (Owner only).
- `POST /trip/{uuid}/join`: Join trip with UUID code.
- `DELETE /trip/{uuid}/member/{member_id}`: Remove member (Owner only).

### Media
- `POST /trip/{uuid}/upload`: Upload media file.
- `GET /trip/{uuid}/gallery`: Fetch gallery listing.
- `GET /media/{uuid}`: Download or stream private file.
- `DELETE /media/{uuid}`: Remove media record and delete file.

---

## Future AWS Migration

This platform is ready to migrate to **Amazon S3** (storage) and **Amazon CloudFront** (high-speed CDN delivery) out-of-the-box. Refer to [migration_guide.md](file:///c:/Users/harsh/Videos/testing/image_upload/docs/migration_guide.md) for step-by-step instructions.
