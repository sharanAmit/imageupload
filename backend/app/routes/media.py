from fastapi import APIRouter, Depends, status, UploadFile, File, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from backend.app.database import get_db
from backend.app.schemas.media import MediaResponse
from backend.app.services.media_service import MediaService
from backend.app.services.auth_service import AuthService
from backend.app.models import User

router = APIRouter(tags=["Media"])

@router.post("/trip/{trip_uuid}/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
def upload_media(
    trip_uuid: str,
    file: UploadFile = File(...),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    return MediaService.upload_media(db, current_user, trip_uuid, file)

@router.get("/trip/{trip_uuid}/gallery", response_model=List[MediaResponse])
def get_gallery(
    trip_uuid: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    return MediaService.get_trip_gallery(db, current_user, trip_uuid)

@router.get("/media", response_model=List[MediaResponse])
def get_all_user_media(
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    return MediaService.get_all_media(db, current_user)

@router.get("/media/{uuid}")
def download_media(
    uuid: str,
    download: bool = False,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    file_path = MediaService.get_media_file_path(db, current_user, uuid)
    
    filename = os.path.basename(file_path)
    # Determine display name or header
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    
    return FileResponse(path=file_path, headers=headers)

@router.delete("/media/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    uuid: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    MediaService.delete_media(db, current_user, uuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
