from sqlalchemy.orm import Session
from backend.app.models import User

class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> User:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_uuid(db: Session, uuid: str) -> User:
        return db.query(User).filter(User.uuid == uuid).first()

    @staticmethod
    def create(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User) -> User:
        db.commit()
        db.refresh(user)
        return user
