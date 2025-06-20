from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.models import SystemPrompt, User
from .schemas import SystemPromptResponse, UserSystemPromptUpdate

def get_system_prompts(db: Session):
    """Получить список всех системных промптов"""
    system_prompts = db.query(SystemPrompt).all()
    return [
        SystemPromptResponse(
            id=prompt.id,
            name=prompt.name,
            text=prompt.text
        ) for prompt in system_prompts
    ]

def update_user_system_prompt(db: Session, user_id: int, prompt_data: UserSystemPromptUpdate):
    """Установить системный промпт для пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    system_prompt = db.query(SystemPrompt).filter(SystemPrompt.id == prompt_data.system_prompt_id).first()
    if not system_prompt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System prompt not found")
    
    user.system_prompt_id = prompt_data.system_prompt_id
    db.commit()
    
    return SystemPromptResponse(
        id=system_prompt.id,
        name=system_prompt.name,
        text=system_prompt.text
    )
    