from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    # pool_pre_ping helps handle database reconnection issues
    pool_pre_ping=True
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy declarative models
Base = declarative_base()

# FastAPI dependency to yield database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
