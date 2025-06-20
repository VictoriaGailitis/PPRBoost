from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from models.models import Chat, Message, User
from .schemas import ChatCreate, MessageCreate, MessageRatingUpdate


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_new_chat(db: Session, chat_data: ChatCreate, user_id: int):
    new_chat = Chat(
        title=chat_data.title,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        is_active=True
    )

    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    return new_chat


def get_all_user_chats(db: Session, user_id: int):
    chats = db.query(Chat).filter(
        Chat.user_id == user_id,
        Chat.is_active == True
    ).order_by(Chat.updated_at.desc()).all()

    return chats


def get_chat_by_id(db: Session, chat_id: int, user_id: int):
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == user_id,
        Chat.is_active == True
    ).first()

    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).all()

    return chat, messages


def delete_chat(db: Session, chat_id: int, user_id: int):
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == user_id,
        Chat.is_active == True
    ).first()

    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    chat.is_active = False
    chat.updated_at = datetime.now(timezone.utc)

    db.commit()
    return True


def update_message_rating(db: Session, rating_data: MessageRatingUpdate, user_id: int):
    message = db.query(Message).join(Chat).filter(
        Message.id == rating_data.message_id,
        Chat.user_id == user_id
    ).first()

    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    message.rating = rating_data.rating
    db.commit()

    return True