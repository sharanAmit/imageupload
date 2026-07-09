from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List

from backend.app.models import User, ActivityLog
from backend.app.repositories.activity_repository import ActivityRepository
from backend.app.repositories.trip_repository import TripRepository
from backend.app.schemas.activity import ActivityLogResponse

class ActivityService:
    @classmethod
    def get_trip_activities(cls, db: Session, user: User, trip_uuid: str, limit: int = 50) -> List[ActivityLogResponse]:
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Verify user is a member of the trip
        member = TripRepository.get_member(db, trip.id, user.id)
        if not member:
            raise HTTPException(status_code=403, detail="Not authorized to view this trip's activities")
            
        logs = ActivityRepository.get_trip_logs(db, trip.id, limit=limit)
        
        # Format list to return with nested user
        return [ActivityLogResponse.model_validate(log) for log in logs]

    @classmethod
    def get_user_activities(cls, db: Session, user: User, limit: int = 50) -> List[ActivityLogResponse]:
        # Get logs associated with current user
        logs = ActivityRepository.get_user_logs(db, user.id, limit=limit)
        return [ActivityLogResponse.model_validate(log) for log in logs]
