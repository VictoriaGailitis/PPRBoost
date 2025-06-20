from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from models.models import User, Message, Chat
from .schemas import RatingCreate

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_message_rating(db: Session, rating_data: RatingCreate, user_id: int):
    chat = db.query(Chat).filter(
        Chat.id == rating_data.chat_id,
        Chat.user_id == user_id,
        Chat.is_active == True
    ).first()
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    message = db.query(Message).filter(
        Message.id == rating_data.message_id,
        Message.chat_id == rating_data.chat_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    
    message.rating = rating_data.rating
    db.commit()
    
    return True

def update_message_rating(db: Session, rating_data: RatingCreate, user_id: int):
    return create_message_rating(db, rating_data, user_id)
