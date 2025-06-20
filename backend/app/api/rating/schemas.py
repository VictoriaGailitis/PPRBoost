from pydantic import BaseModel
from typing import Optional

class RatingBase(BaseModel):
    message_id: int
    rating: int
    
class RatingCreate(RatingBase):
    chat_id: int

class RatingResponse(RatingBase):
    id: int
    
    class Config:
        orm_mode = True
