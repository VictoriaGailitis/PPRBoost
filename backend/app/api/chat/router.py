from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session
from typing import List

from core.database import get_session
from core.security import get_current_user_id
from .schemas import ChatCreate, ChatResponse, ChatListResponse, ChatDetailResponse, MessageBase
from .service import create_new_chat, get_all_user_chats, get_chat_by_id, delete_chat

chat = APIRouter(tags=["Chat"])

@chat.post("/create_chat", response_model=ChatResponse)
def create_chat(
    chat_data: ChatCreate, 
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    new_chat = create_new_chat(db, chat_data, user_id)
    return new_chat

@chat.get("/chats", response_model=List[ChatResponse])
def get_all_chats(
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    chats = get_all_user_chats(db, user_id)
    return chats

@chat.get("/chat/{chat_id}", response_model=ChatDetailResponse)
def get_current_chat(
    chat_id: int = Path(...),
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    chat_obj, messages = get_chat_by_id(db, chat_id, user_id)
    
    chat_response = ChatDetailResponse(
        id=chat_obj.id,
        title=chat_obj.title,
        created_at=chat_obj.created_at,
        updated_at=chat_obj.updated_at,
        is_active=chat_obj.is_active,
        messages=[
            MessageBase(
                id=message.id,
                chat_id=message.chat_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                rating=message.rating
            ) for message in messages
        ]
    )
    
    return chat_response

@chat.delete("/chat/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_handler(
    chat_id: int = Path(...),
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    delete_chat(db, chat_id, user_id)
    return None