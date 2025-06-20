from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_session
from core.security import get_current_user_id
from .schemas import RatingCreate, RatingResponse
from .service import create_message_rating, update_message_rating

rating = APIRouter(tags=["Rating"])

@rating.post("/rate_message", status_code=status.HTTP_200_OK)
def rate_message(
    rating_data: RatingCreate,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    create_message_rating(db, rating_data, user_id)
    return {"message": "Rating created successfully"}

@rating.patch("/update_rating", status_code=status.HTTP_200_OK)
def update_rating(
    rating_data: RatingCreate,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    update_message_rating(db, rating_data, user_id)
    return {"message": "Rating updated successfully"}