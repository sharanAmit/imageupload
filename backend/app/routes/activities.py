from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.schemas.activity import ActivityLogResponse
from backend.app.services.activity_service import ActivityService
from backend.app.services.auth_service import AuthService
from backend.app.models import User

router = APIRouter(tags=["Activities"])

@router.get("/trip/{trip_uuid}/activities", response_model=List[ActivityLogResponse])
def get_trip_activities(
    trip_uuid: str,
    limit: int = 50,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    return ActivityService.get_trip_activities(db, current_user, trip_uuid, limit)

@router.get("/activities/me", response_model=List[ActivityLogResponse])
def get_my_activities(
    limit: int = 50,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    return ActivityService.get_user_activities(db, current_user, limit)
