import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from contextlib import asynccontextmanager
import sys

from backend.app.config import settings
from backend.app.database import engine, Base, run_schema_migrations
from backend.app.routes import auth, trips, media, activities, users
from backend.app.middlewares.error_handler import error_handling_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup (convenient fallback)
    # Skip database initialization if running inside a pytest testing context
    if "pytest" not in sys.modules:
        Base.metadata.create_all(bind=engine)
        run_schema_migrations()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A private, self-hosted Trip Memories Platform APIs",
    version="1.0.0",
    lifespan=lifespan
)


# CORS Configuration
# Allow local developments (e.g. Live Server or other frontend origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Error Interception Middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=error_handling_middleware)

# Ensure the upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Mount Local Uploads Statically
# Allows static file serving at '/uploads/...'
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(media.router)
app.include_router(activities.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API!",
        "docs_url": "/docs",
        "status": "healthy"
    }
