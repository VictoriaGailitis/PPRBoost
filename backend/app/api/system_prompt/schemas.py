from pydantic import BaseModel
from typing import List

class SystemPromptResponse(BaseModel):
    id: int
    name: str
    text: str

class SystemPromptListResponse(BaseModel):
    prompts: List[SystemPromptResponse]

class UserSystemPromptUpdate(BaseModel):
    system_prompt_id: int


