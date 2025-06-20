from pydantic import BaseModel

class ChatMessage(BaseModel):
    message: str
    reasoning: bool = False
    chat_id: int

class ChatMessageWithAttachments(ChatMessage):
    attachments: list[tuple[str, str]]

class CategoryRequest(BaseModel):
    text: str
    chat_id: int

class CategoryResponse(BaseModel):
    category_level_1: str | None
    category_level_2: str | None

class RagbotResponse(BaseModel):
    text: str 
    sources: list[dict] | None
    
class FileUploadResponse(BaseModel):
    original_filename: str
    file_path: str
    attachment_format: list[tuple[str, str]]
    