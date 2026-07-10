from sqlalchemy import create_engine, inspect, text
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

def run_schema_migrations():
    """Lightweight, additive schema patch for existing SQLite/Postgres databases
    created before new nullable/defaulted columns were introduced (no Alembic in this project)."""
    inspector = inspect(engine)
    if "trip_invites" not in inspector.get_table_names():
        return
    columns = [c["name"] for c in inspector.get_columns("trip_invites")]
    if "status" not in columns:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE trip_invites ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'"
            ))
            conn.execute(text(
                "UPDATE trip_invites SET status = 'accepted' WHERE used = true"
            ))
