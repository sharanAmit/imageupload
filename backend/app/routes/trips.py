from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.schemas.trip import TripCreate, TripUpdate, TripResponse, TripDetailResponse, TripInviteRequest, TripMemberResponse
from backend.app.services.trip_service import TripService
from backend.app.services.auth_service import AuthService
from backend.app.models import User

router = APIRouter(prefix="/trip", tags=["Trips"])

@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    data: TripCreate, 
    current_user: User = Depends(AuthService.get_current_user), 
    db: Session = Depends(get_db)
):
    return TripService.create_trip(db, current_user, data)

@router.get("", response_model=List[TripResponse])
def list_trips(
    current_user: User = Depends(AuthService.get_current_user), 
    db: Session = Depends(get_db)
):
    return TripService.get_user_trips(db, current_user)

@router.get("/{uuid}", response_model=TripDetailResponse)
def get_trip_details(
    uuid: str, 
    current_user: User = Depends(AuthService.get_current_user), 
    db: Session = Depends(get_db)
):
    return TripService.get_trip_details(db, current_user, uuid)

@router.put("/{uuid}", response_model=TripResponse)
def update_trip(
    uuid: str, 
    data: TripUpdate, 
    current_user: User = Depends(AuthService.get_current_user), 
    db: Session = Depends(get_db)
):
    return TripService.update_trip(db, current_user, uuid, data)

@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    uuid: str, 
    current_user: User = Depends(AuthService.get_current_user), 
    db: Session = Depends(get_db)
):
    TripService.delete_trip(db, current_user, uuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{uuid}/invite", response_model=TripMemberResponse)
def invite_member(
    uuid: str, 
    data: TripInviteRequest, 
    current_user: User = Depends(AuthService.get_current_user), 
    db: Session = Depends(get_db)
):
    return TripService.invite_member(db, current_user, uuid, data)

@router.post("/{uuid}/join", response_model=TripMemberResponse)
def join_trip(
    uuid: str, 
    current_user: User = Depends(AuthService.get_current_user), 
    db: Session = Depends(get_db)
):
    return TripService.join_trip(db, current_user, uuid)

@router.delete("/{uuid}/member/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    uuid: str, 
    member_id: int, 
    current_user: User = Depends(AuthService.get_current_user), 
    db: Session = Depends(get_db)
):
    TripService.remove_member(db, current_user, uuid, member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{uuid}/member/{member_id}/role", response_model=TripMemberResponse)
def update_member_role(
    uuid: str,
    member_id: int,
    payload: dict,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    role = payload.get("role")
    from fastapi import HTTPException
    if role not in ["member", "co-owner"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    return TripService.update_member_role(db, current_user, uuid, member_id, role)

