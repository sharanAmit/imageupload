from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from backend.app.models import Trip, TripMember, User

class TripRepository:
    @staticmethod
    def get_by_id(db: Session, trip_id: int) -> Optional[Trip]:
        return db.query(Trip).filter(Trip.id == trip_id).first()

    @staticmethod
    def get_by_uuid(db: Session, uuid: str) -> Optional[Trip]:
        return db.query(Trip).filter(Trip.uuid == uuid).first()

    @staticmethod
    def get_user_trips(db: Session, user_id: int) -> List[Trip]:
        # Return trips where user is the creator OR a member of the trip
        return db.query(Trip).join(TripMember, TripMember.trip_id == Trip.id, isouter=True).filter(
            or_(Trip.created_by == user_id, TripMember.user_id == user_id)
        ).distinct().order_by(Trip.created_at.desc()).all()

    @staticmethod
    def create(db: Session, trip: Trip) -> Trip:
        db.add(trip)
        db.commit()
        db.refresh(trip)
        return trip

    @staticmethod
    def update(db: Session, trip: Trip) -> Trip:
        db.commit()
        db.refresh(trip)
        return trip

    @staticmethod
    def delete(db: Session, trip: Trip) -> None:
        db.delete(trip)
        db.commit()

    @staticmethod
    def add_member(db: Session, trip_id: int, user_id: int, role: str = "member") -> TripMember:
        member = TripMember(trip_id=trip_id, user_id=user_id, role=role)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def get_member(db: Session, trip_id: int, user_id: int) -> Optional[TripMember]:
        return db.query(TripMember).filter(
            TripMember.trip_id == trip_id, 
            TripMember.user_id == user_id
        ).first()

    @staticmethod
    def get_members(db: Session, trip_id: int) -> List[TripMember]:
        return db.query(TripMember).filter(TripMember.trip_id == trip_id).all()

    @staticmethod
    def remove_member(db: Session, member: TripMember) -> None:
        db.delete(member)
        db.commit()
