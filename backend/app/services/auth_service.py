from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from backend.app.config import settings
from backend.app.models import User
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.user import UserCreate, UserChangePassword, Token
from backend.app.database import get_db

# Direct bcrypt is used for modern Python 3.14+ compatibility

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        # bcrypt.hashpw expects bytes. We encode the password string.
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False

    @staticmethod
    def create_token(data: dict, expires_delta: timedelta, is_refresh: bool = False) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({
            "exp": expire,
            "type": "refresh" if is_refresh else "access"
        })
        secret = settings.JWT_REFRESH_SECRET_KEY if is_refresh else settings.JWT_SECRET_KEY
        return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)

    @classmethod
    def generate_tokens(cls, user: User) -> Token:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = cls.create_token(
            data={"sub": user.email, "user_id": user.id}, 
            expires_delta=access_token_expires
        )
        refresh_token = cls.create_token(
            data={"sub": user.email, "user_id": user.id}, 
            expires_delta=refresh_token_expires,
            is_refresh=True
        )
        return Token(access_token=access_token, refresh_token=refresh_token)

    @classmethod
    def register_user(cls, db: Session, user_data: UserCreate, invite_token: Optional[str] = None) -> User:
        # Check if email exists
        existing_user = UserRepository.get_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Verify invite token if provided
        invite = None
        if invite_token:
            from backend.app.models import TripInvite
            invite = db.query(TripInvite).filter(
                TripInvite.uuid == invite_token,
                TripInvite.status == "pending"
            ).first()
            if not invite:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid or expired invite token"
                )
            # Ensure they register with the invited email address!
            if invite.email.lower() != user_data.email.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This registration email does not match the invited address."
                )

        hashed_password = cls.hash_password(user_data.password)
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password
        )
        created_user = UserRepository.create(db, new_user)
        
        # If there was an invite, automatically join them to the trip!
        if invite:
            from backend.app.repositories.trip_repository import TripRepository
            from backend.app.repositories.activity_repository import ActivityRepository
            
            # Add member
            TripRepository.add_member(db, invite.trip_id, created_user.id, invite.role)

            # Registering via the invite link is how a new user accepts the invite
            invite.status = "accepted"
            db.commit()
            
            # Log join activity
            ActivityRepository.create_log(
                db=db,
                user_id=created_user.id,
                trip_id=invite.trip_id,
                action="joined_trip",
                target_id=invite.uuid
            )

        return created_user

    @classmethod
    def authenticate_user(cls, db: Session, email: str, password: str) -> Token:
        user = UserRepository.get_by_email(db, email)
        if not user or not cls.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return cls.generate_tokens(user)

    @classmethod
    def refresh_tokens(cls, db: Session, refresh_token: str) -> Token:
        try:
            payload = jwt.decode(
                refresh_token, 
                settings.JWT_REFRESH_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            if email is None or token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user = UserRepository.get_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return cls.generate_tokens(user)

    @classmethod
    def get_current_user(
        cls, 
        request: Request,
        db: Session = Depends(get_db), 
        token: Optional[str] = Depends(oauth2_scheme)
    ) -> User:
        # Standard oauth2 scheme returns the token from the Header
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        # We check the Authorization header first, and fall back to 'token' query param
        resolved_token = token
        if not resolved_token:
            resolved_token = request.query_params.get("token")
            
        if not resolved_token:
            raise credentials_exception
        
        try:
            payload = jwt.decode(resolved_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            if email is None or token_type != "access":
                raise credentials_exception
        except JWTError:
            raise credentials_exception
            
        user = UserRepository.get_by_email(db, email)
        if user is None:
            raise credentials_exception
        return user

    @classmethod
    def change_password(cls, db: Session, user: User, data: UserChangePassword) -> User:
        if not cls.verify_password(data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        user.password_hash = cls.hash_password(data.new_password)
        return UserRepository.update(db, user)

    @classmethod
    def authenticate_google_user(cls, db: Session, id_token: str, invite_token: Optional[str] = None) -> Token:
        import httpx
        import uuid
        from backend.app.repositories.activity_repository import ActivityRepository

        # Verify Google ID Token via Google's tokeninfo API
        try:
            response = httpx.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
                timeout=10.0
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Google ID Token"
                )
            
            payload = response.json()
            
            # Verify client ID audience if configured
            if settings.GOOGLE_CLIENT_ID and payload.get("aud") != settings.GOOGLE_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google Token audience mismatch"
                )
                
            email = payload.get("email")
            name = payload.get("name", email.split("@")[0])
            picture = payload.get("picture")
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google profile does not contain email"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Google auth service unavailable: {str(e)}"
            )
            
        # Check if user already exists
        user = UserRepository.get_by_email(db, email)
        if not user:
            # Automatic registration for Google SSO users
            random_password = str(uuid.uuid4())
            user = User(
                name=name,
                email=email,
                password_hash=cls.hash_password(random_password),
                profile_image=picture
            )
            user = UserRepository.create(db, user)
            
            # Log registration activity
            ActivityRepository.create_log(
                db=db,
                user_id=user.id,
                trip_id=None,
                action="registered_via_google",
                target_id=user.uuid
            )
        else:
            # Sync user's profile image if it was updated on Google
            if picture and user.profile_image != picture:
                user.profile_image = picture
                UserRepository.update(db, user)
                
        # Process invitation if token is provided
        if invite_token:
            from backend.app.models import TripInvite
            from backend.app.repositories.trip_repository import TripRepository
            
            invite = db.query(TripInvite).filter(
                TripInvite.uuid == invite_token,
                TripInvite.status == "pending"
            ).first()

            if invite:
                # Ensure the invited email matches the Google user email (case-insensitive)
                if invite.email.lower() == email.lower():
                    # Check if already a member
                    existing_member = TripRepository.get_member(db, invite.trip_id, user.id)
                    if not existing_member:
                        # Add as member with target role
                        TripRepository.add_member(db, invite.trip_id, user.id, invite.role)

                        # Signing in via the invite link is how the user accepts the invite
                        invite.status = "accepted"
                        db.commit()
                        
                        # Log activity
                        ActivityRepository.create_log(
                            db=db,
                            user_id=user.id,
                            trip_id=invite.trip_id,
                            action="joined_trip",
                            target_id=invite.uuid
                        )
                
        return cls.generate_tokens(user)

