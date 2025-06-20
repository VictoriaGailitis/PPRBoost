from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MessageBase(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime
    rating: Optional[int] = None

    class Config:
        orm_mode = True


class ChatBase(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True


class ChatCreate(BaseModel):
    title: str = "Новый чат"


class ChatResponse(ChatBase):
    pass


class ChatListResponse(BaseModel):
    chats: List[ChatBase]


class ChatDetailResponse(ChatBase):
    messages: List[MessageBase] = []


class MessageCreate(BaseModel):
    content: str
    role: str = "user"


class MessageRatingUpdate(BaseModel):
    message_id: int
    rating: int