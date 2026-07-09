import uuid
import os
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status
from typing import List, Optional

from backend.app.config import settings
from backend.app.models import Media, User
from backend.app.repositories.media_repository import MediaRepository
from backend.app.repositories.trip_repository import TripRepository
from backend.app.repositories.activity_repository import ActivityRepository
from backend.app.services.storage import StorageService, get_storage_service
from backend.app.schemas.media import MediaResponse

class MediaService:
    @classmethod
    def upload_media(
        cls, 
        db: Session, 
        user: User, 
        trip_uuid: str, 
        file: UploadFile,
        storage_service: StorageService = None
    ) -> MediaResponse:
        if storage_service is None:
            storage_service = get_storage_service()
            
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Verify user is a member of the trip
        member = TripRepository.get_member(db, trip.id, user.id)
        if not member:
            raise HTTPException(status_code=403, detail="Not authorized to upload to this trip")
            
        # Determine file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # Reset file cursor
            
        # Validate extension
        filename_parts = file.filename.split(".")
        if len(filename_parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid file name")
        extension = filename_parts[-1].lower()
        
        # Determine media type
        if extension in settings.ALLOWED_IMAGE_EXTENSIONS:
            media_type = "photo"
        elif extension in settings.ALLOWED_VIDEO_EXTENSIONS:
            media_type = "video"
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file extension. Allowed images: JPG, PNG, WEBP, GIF. Videos: MP4, MOV, WEBM."
            )
            
        # Generate clean storage key: trips/{trip_uuid}/{photos|videos}/{unique_id}.{ext}
        folder_name = "photos" if media_type == "photo" else "videos"
        unique_filename = f"{uuid.uuid4()}.{extension}"
        storage_key = f"trips/{trip_uuid}/{folder_name}/{unique_filename}"
        
        # Upload using StorageService
        storage_service.upload(file, storage_key)
        
        # Create media record in DB
        media_record = Media(
            trip_id=trip.id,
            uploaded_by=user.id,
            media_type=media_type,
            storage_key=storage_key,
            file_size=file_size,
            mime_type=file.content_type or f"{media_type}/{extension}"
        )
        created_media = MediaRepository.create(db, media_record)
        
        # Log activity
        ActivityRepository.create_log(
            db=db, 
            user_id=user.id, 
            trip_id=trip.id, 
            action="uploaded_media",
            target_id=created_media.uuid
        )
        
        # Map to response schema and attach dynamic URL
        response = MediaResponse.model_validate(created_media)
        response.url = storage_service.get_url(storage_key)
        return response

    @classmethod
    def get_trip_gallery(
        cls, 
        db: Session, 
        user: User, 
        trip_uuid: str,
        storage_service: StorageService = None
    ) -> List[MediaResponse]:
        if storage_service is None:
            storage_service = get_storage_service()
            
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Verify user is a member of the trip
        member = TripRepository.get_member(db, trip.id, user.id)
        if not member:
            raise HTTPException(status_code=403, detail="Not authorized to view this trip gallery")
            
        media_list = MediaRepository.get_trip_gallery(db, trip.id)
        
        # Convert and attach URL
        result = []
        for media in media_list:
            res = MediaResponse.model_validate(media)
            res.url = storage_service.get_url(media.storage_key)
            res.trip_name = trip.trip_name
            result.append(res)
            
        return result

    @classmethod
    def get_media_file_path(
        cls, 
        db: Session, 
        user: User, 
        media_uuid: str,
        storage_service: StorageService = None
    ) -> str:
        if storage_service is None:
            storage_service = get_storage_service()
            
        media = MediaRepository.get_by_uuid(db, media_uuid)
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
            
        # Verify user is member of trip
        member = TripRepository.get_member(db, media.trip_id, user.id)
        if not member:
            raise HTTPException(status_code=403, detail="Not authorized to view this media")
            
        return storage_service.get_file_path(media.storage_key)

    @classmethod
    def delete_media(
        cls, 
        db: Session, 
        user: User, 
        media_uuid: str,
        storage_service: StorageService = None
    ) -> None:
        if storage_service is None:
            storage_service = get_storage_service()
            
        media = MediaRepository.get_by_uuid(db, media_uuid)
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
            
        trip = TripRepository.get_by_id(db, media.trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Get memberships for permission validation
        curr_member = TripRepository.get_member(db, trip.id, user.id)
        if not curr_member:
            raise HTTPException(status_code=403, detail="Not authorized to perform this action")
            
        # Verify permissions: Owner can delete any media. Member can delete own media.
        is_owner = (curr_member.role == "owner")
        is_uploader = (media.uploaded_by == user.id)
        
        if not (is_owner or is_uploader):
            raise HTTPException(
                status_code=403, 
                detail="Only the media uploader or the trip owner can delete this media"
            )
            
        # Delete file from storage
        storage_service.delete(media.storage_key)
        
        # Delete DB record
        MediaRepository.delete(db, media)
        
        # Log activity
        ActivityRepository.create_log(
            db=db, 
            user_id=user.id, 
            trip_id=trip.id, 
            action="deleted_media",
            target_id=media_uuid
        )

    @classmethod
    def get_all_media(
        cls, 
        db: Session, 
        user: User, 
        storage_service: StorageService = None
    ) -> List[MediaResponse]:
        if storage_service is None:
            storage_service = get_storage_service()
            
        user_trips = TripRepository.get_user_trips(db, user.id)
        trip_ids = [t.id for t in user_trips]
        
        if not trip_ids:
            return []
            
        media_list = db.query(Media).filter(Media.trip_id.in_(trip_ids)).order_by(Media.created_at.desc()).all()
        
        result = []
        for media in media_list:
            res = MediaResponse.model_validate(media)
            res.url = storage_service.get_url(media.storage_key)
            res.trip_name = media.trip.trip_name
            result.append(res)
            
        return result

