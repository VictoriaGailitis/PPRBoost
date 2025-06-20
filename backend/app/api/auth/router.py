import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .schemas import UserCreate, Token, UserLogin, SystemPromptResponse
from .service import authenticate_user, create_user, get_user_info_from_token, get_system_prompt
from core.security import create_access_token, decode_access_token
from core.database import get_session

logger = logging.getLogger(__name__)

auth = APIRouter(tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

@auth.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_session)):
    user = authenticate_user(db, user_data.email, user_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    
    system_prompt_data = SystemPromptResponse()  
    if user.system_prompt:
        system_prompt_data = SystemPromptResponse(
            id=user.system_prompt.id,
            name=user.system_prompt.name,
            text=user.system_prompt.text
        )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "system_prompt": system_prompt_data
    }

@auth.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_session)):
    new_user = create_user(db, user)
    
    access_token = create_access_token(data={"sub": new_user.email, "id": new_user.id})

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "system_prompt": SystemPromptResponse()
    }

@auth.get("/users/me")
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        
        user = get_user_info_from_token(db, email)
        
        system_prompt_data = SystemPromptResponse()  
        if user.system_prompt:
            system_prompt_data = SystemPromptResponse(
                id=user.system_prompt.id,
                name=user.system_prompt.name,
                text=user.system_prompt.text
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "system_prompt": system_prompt_data
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@auth.post("/token", response_model=Token)
def login_for_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    
    system_prompt_data = SystemPromptResponse()
    if user.system_prompt:
        system_prompt_data = SystemPromptResponse(
            id=user.system_prompt.id,
            name=user.system_prompt.name,
            text=user.system_prompt.text
        )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "system_prompt": system_prompt_data
    }