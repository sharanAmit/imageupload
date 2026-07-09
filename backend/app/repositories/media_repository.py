from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.models import Media

class MediaRepository:
    @staticmethod
    def get_by_id(db: Session, media_id: int) -> Optional[Media]:
        return db.query(Media).filter(Media.id == media_id).first()

    @staticmethod
    def get_by_uuid(db: Session, uuid: str) -> Optional[Media]:
        return db.query(Media).filter(Media.uuid == uuid).first()

    @staticmethod
    def get_trip_gallery(db: Session, trip_id: int) -> List[Media]:
        return db.query(Media).filter(Media.trip_id == trip_id).order_by(Media.created_at.desc()).all()

    @staticmethod
    def create(db: Session, media: Media) -> Media:
        db.add(media)
        db.commit()
        db.refresh(media)
        return media

    @staticmethod
    def delete(db: Session, media: Media) -> None:
        db.delete(media)
        db.commit()
