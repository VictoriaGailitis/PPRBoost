from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from core.database import get_session
from core.security import get_current_user_id
from .service import get_system_prompts, update_user_system_prompt
from .schemas import SystemPromptResponse, UserSystemPromptUpdate

system_prompt = APIRouter(tags=["System Prompt"])

@system_prompt.get("/system_prompts", response_model=List[SystemPromptResponse])
def get_all_system_prompts(db: Session = Depends(get_session)):
    """Получить список всех системных промптов"""
    return get_system_prompts(db)

@system_prompt.post("/system_prompt", response_model=SystemPromptResponse)
def update_user_prompt(
    prompt_data: UserSystemPromptUpdate,
    db: Session = Depends(get_session),
    user_id: int = Depends(get_current_user_id)
):
    """Установить системный промпт для текущего пользователя"""
    return update_user_system_prompt(db, user_id, prompt_data)

