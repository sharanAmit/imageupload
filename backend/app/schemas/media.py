from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MediaResponse(BaseModel):
    id: int
    uuid: str
    trip_id: int
    uploaded_by: int
    media_type: str  # 'photo', 'video'
    storage_key: str
    file_size: int
    mime_type: str
    created_at: datetime
    url: Optional[str] = None  # Populated dynamically by storage service
    trip_name: Optional[str] = None

    class Config:
        from_attributes = True
