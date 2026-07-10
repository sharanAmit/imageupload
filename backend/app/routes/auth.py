from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserChangePassword
from backend.app.services.auth_service import AuthService
from backend.app.models import User
from backend.app.config import settings

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, invite_token: Optional[str] = None, db: Session = Depends(get_db)):
    return AuthService.register_user(db, user_data, invite_token)

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    return AuthService.authenticate_user(db, credentials.email, credentials.password)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(AuthService.get_current_user)):
    return current_user

@router.post("/refresh", response_model=Token)
def refresh_token(payload: dict, db: Session = Depends(get_db)):
    # Expecting refresh token in JSON payload: {"refresh_token": "..."}
    ref_token = payload.get("refresh_token")
    return AuthService.refresh_tokens(db, ref_token)

@router.post("/change-password", response_model=UserResponse)
def change_password(
    data: UserChangePassword, 
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    return AuthService.change_password(db, current_user, data)

@router.post("/logout")
def logout():
    # Since JWT is stateless, logout is handled client-side by deleting tokens.
    # We return a success message here.
    return {"detail": "Successfully logged out"}

@router.post("/auth/google", response_model=Token)
def login_google(payload: dict, invite_token: Optional[str] = None, db: Session = Depends(get_db)):
    id_token = payload.get("id_token")
    return AuthService.authenticate_google_user(db, id_token, invite_token)

@router.get("/auth/config")
def get_auth_config():
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID
    }

@router.get("/auth/invite/{token}")
def get_invite_details(token: str, db: Session = Depends(get_db)):
    from backend.app.models import TripInvite
    from backend.app.repositories.user_repository import UserRepository
    # We need Session to query, which is why get_db depends
    invite = db.query(TripInvite).filter(
        TripInvite.uuid == token,
        TripInvite.status == "pending"
    ).first()
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite token not found, already responded to, or expired."
        )
    return {
        "trip_name": invite.trip.trip_name,
        "email": invite.email,
        "role": invite.role,
        "account_exists": UserRepository.get_by_email(db, invite.email) is not None
    }


