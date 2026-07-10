import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    profile_image = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    trips_created = relationship("Trip", back_populates="creator")
    memberships = relationship("TripMember", back_populates="user", cascade="all, delete-orphan")
    media_uploaded = relationship("Media", back_populates="uploader")
    activities = relationship("ActivityLog", back_populates="user")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=generate_uuid)
    trip_name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    cover_image = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="trips_created")
    members = relationship("TripMember", back_populates="trip", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="trip", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="trip", cascade="all, delete-orphan")
    invites = relationship("TripInvite", back_populates="trip", cascade="all, delete-orphan")


class TripMember(Base):
    __tablename__ = "trip_members"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False, default="member")  # 'owner', 'member'
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    trip = relationship("Trip", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=generate_uuid)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    media_type = Column(String(50), nullable=False)  # 'photo', 'video'
    storage_key = Column(String(255), nullable=False)  # e.g. trips/uuid/photos/filename.jpg
    file_size = Column(BigInteger, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    trip = relationship("Trip", back_populates="media")
    uploader = relationship("User", back_populates="media_uploaded")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)  # nullable in case of global logs
    action = Column(String(255), nullable=False)  # e.g., 'created_trip', 'uploaded_media', etc.
    target_id = Column(String(255), nullable=True)  # UUID of target user/media/trip
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="activities")
    trip = relationship("Trip", back_populates="activities")


class TripInvite(Base):
    __tablename__ = "trip_invites"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=generate_uuid)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), index=True, nullable=False)
    role = Column(String(50), default="member", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # 'pending', 'accepted', 'declined'

    # Relationships
    trip = relationship("Trip", back_populates="invites")

