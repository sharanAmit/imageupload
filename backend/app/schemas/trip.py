from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from backend.app.schemas.user import UserResponse

class TripBase(BaseModel):
    trip_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class TripCreate(TripBase):
    cover_image: Optional[str] = None

class TripUpdate(BaseModel):
    trip_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    cover_image: Optional[str] = None

class TripResponse(TripBase):
    id: int
    uuid: str
    cover_image: Optional[str] = None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class TripMemberResponse(BaseModel):
    id: int
    trip_id: int
    user_id: int
    role: str
    joined_at: datetime
    status: str = "accepted"  # 'pending', 'accepted', 'declined' (invites only; real members are always 'accepted')
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True

class TripInviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"  # 'owner', 'member'

class TripDetailResponse(TripResponse):
    members: List[TripMemberResponse] = []
    
    class Config:
        from_attributes = True
