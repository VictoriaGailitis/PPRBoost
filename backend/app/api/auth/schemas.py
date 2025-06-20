from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SystemPrompt(BaseModel):
    id: int
    name: str
    text: str

class SystemPromptResponse(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    text: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    system_prompt: Optional[SystemPromptResponse] = None

