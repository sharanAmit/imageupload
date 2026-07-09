from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from backend.app.schemas.user import UserResponse

class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    trip_id: Optional[int] = None
    action: str
    target_id: Optional[str] = None
    created_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True
