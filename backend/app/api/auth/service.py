from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.security import get_password_hash, verify_password
from models.models import User, SystemPrompt
from .schemas import UserCreate

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = get_password_hash(user.password)

    new_user = User(
        email=user.email,
        username=user.email.split('@')[0],
        password=hashed_password,
        is_active=True,
        date_joined=datetime.now(timezone.utc)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    return user

def get_system_prompt(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user or not user.system_prompt_id:
        return None
    return db.query(SystemPrompt).filter(SystemPrompt.id == user.system_prompt_id).first()

def get_user_info_from_token(db: Session, email: str):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user