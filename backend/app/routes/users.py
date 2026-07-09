from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.schemas.user import UserResponse
from backend.app.services.auth_service import AuthService
from backend.app.models import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/search", response_model=List[UserResponse])
def search_users(
    q: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    if not q.strip():
        return []
    
    query = f"%{q.strip()}%"
    matched_users = db.query(User).filter(
        User.id != current_user.id,
        (User.name.ilike(query)) | (User.email.ilike(query))
    ).limit(10).all()
    
    return matched_users
