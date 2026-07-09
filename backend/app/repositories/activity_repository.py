from sqlalchemy.orm import Session
from typing import List
from backend.app.models import ActivityLog

class ActivityRepository:
    @staticmethod
    def create_log(db: Session, user_id: int, trip_id: int, action: str, target_id: str = None) -> ActivityLog:
        log = ActivityLog(
            user_id=user_id,
            trip_id=trip_id,
            action=action,
            target_id=target_id
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_trip_logs(db: Session, trip_id: int, limit: int = 50) -> List[ActivityLog]:
        return db.query(ActivityLog).filter(
            ActivityLog.trip_id == trip_id
        ).order_by(ActivityLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_user_logs(db: Session, user_id: int, limit: int = 50) -> List[ActivityLog]:
        return db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id
        ).order_by(ActivityLog.created_at.desc()).limit(limit).all()
