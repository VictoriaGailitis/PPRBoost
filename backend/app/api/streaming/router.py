import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Query, Request, Depends, HTTPException, status, BackgroundTasks, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
from typing import AsyncGenerator
import asyncio
from sqlalchemy.orm import Session

from .ragbot_vllm import RAGChatBot as Ragbot
from .schemas import ChatMessage, ChatMessageWithAttachments, CategoryRequest, CategoryResponse, RagbotResponse, FileUploadResponse
from .service import categorize_text, get_user_system_prompt, get_active_configuration, get_active_thinking_configuration
from core.security import decode_access_token
from core.database import get_session
from models.models import Message, Category

router = APIRouter(prefix="/streaming", tags=["streaming"])
security = HTTPBearer()

# Создаем функцию для инициализации Ragbot с актуальными моделями
def get_ragbot(db: Session, llm_model: str = 'trained_ppr_gemma/gemma-2-9b-it-4bit', embeddings_model: str) -> Ragbot:
    embeddings_model_path = f'/app/llms/hub/models--{embeddings_model.replace("/", "--")}'
    return Ragbot(
        model_name=llm_model,
        save_path='./vector_store_1',
        system_prompt='Ты — интеллектуальный ассистент, отвечающий на вопросы пользователей на основе базы знаний ППР. В случае, если вопрос касается запрещенных тем или провокацию игнорируй его.',
        data_sources=[
            ('file', './data/doc1.pdf'), # PDF
            ('file', './data/doc2.pdf'), # PDF
            ('file', './data/doc3.pdf'), # PDF
            ('file', './data/doc4.pdf'), # PDF
            ('file', './data/doc5.pdf'),
        ],
        embeddings_model=embeddings_model_path,
    )

async def generate_chunks(
    message: str,
    chat_id: int,
    user_id: int,
    db: Session
) -> AsyncGenerator[bytes, None]:
    try:
        # Получаем и устанавливаем системный промпт пользователя
        system_prompt = await get_user_system_prompt(db, user_id)
        ragbot = get_ragbot(db)
        if system_prompt:
            ragbot.change_prompt(system_prompt)

        answer, _ = ragbot.chat(message)
        # Разбиваем ответ на чанки примерно по 100 символов
        chunk_size = 100
        chunks = [answer[i:i + chunk_size] for i in range(0, len(answer), chunk_size)]
        
        buffer = []
        for chunk in chunks:
            buffer.append(chunk)
            if len(buffer) >= 5:  # Отправляем каждые 5 чанков
                yield json.dumps({"text": "".join(buffer)}).encode() + b"\n"
                buffer = []
            await asyncio.sleep(0.01)
        
        if buffer:  # Отправляем оставшиеся чанки
            yield json.dumps({"text": "".join(buffer)}).encode() + b"\n"
    except Exception as e:
        yield json.dumps({"error": str(e)}).encode() + b"\n"

@router.post("/stream")
async def chat_stream(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
):
    try:
        # Проверяем токен авторизации
        user = decode_access_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Получаем данные из запроса
        data = await request.json()
        message = ChatMessage(
            message=data["message"],
            chat_id=int(data["chat_id"])
        )
        
        return StreamingResponse(
            generate_chunks(
                message.message,
                message.chat_id,
                user["id"],
                db
            ),
            media_type="application/x-ndjson"
        )
    except HTTPException:
        raise
    except Exception as e:
        return StreamingResponse(
            iter([json.dumps({"error": str(e)}).encode() + b"\n"]),
            media_type="application/x-ndjson"
        )

@router.post("/chat", response_model=RagbotResponse)
async def chat_request(
    message: ChatMessage,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
):
    try:
        user = decode_access_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        system_prompt = await get_user_system_prompt(db, user["id"])
        if message.reasoning:
            llm_model, embeddings_model = get_active_thinking_configuration(db)
        else:
            llm_model, embeddings_model = get_active_configuration(db)
        ragbot = get_ragbot(db, llm_model, embeddings_model)
        if system_prompt:
            ragbot.change_prompt(system_prompt)
            
        answer, sources = ragbot.chat(message.message)
        
        # Сохраняем ответ ассистента
        assistant_message = Message(
            chat_id=message.chat_id,
            role="assistant",
            content=answer,
            created_at=datetime.utcnow()
        )
        db.add(assistant_message)
        db.commit()
        
        formatted_sources = [
            {
                'source': source.metadata['source'].replace('/content/', '/data/'), 
                'page': source.metadata['page'], 
                'quote': source.page_content
            } 
            for source in sources
        ] if sources else None
        
        return RagbotResponse(text=answer, sources=formatted_sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat_with_attachments", response_model=RagbotResponse)
async def chat_with_attachments(
    message: ChatMessageWithAttachments,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
):
    try:
        user = decode_access_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        system_prompt = await get_user_system_prompt(db, user["id"])
        if message.reasoning:
            llm_model, embeddings_model = get_active_thinking_configuration(db)
        else:
            llm_model, embeddings_model = get_active_configuration(db)  
        ragbot = get_ragbot(db, llm_model, embeddings_model)
        if system_prompt:
            ragbot.change_prompt(system_prompt)

        # Определяем тип вложения
        request_type = None
        if message.attachments:
            attachment = message.attachments[0][1]  
            # Проверяем, является ли attachment URL-адресом
            if isinstance(attachment, str) and attachment.startswith(('http://', 'https://')):
                request_type = "url"
            else:
                file_extension = os.path.splitext(attachment)[1].lower()
                if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']:
                    request_type = "image"
                elif file_extension in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']:
                    request_type = "audio"
                else:
                    request_type = "file"
                    supported_file_extensions = [
                        '.txt', '.pdf', '.doc', '.docx', '.pptx', '.csv', '.html', '.htm',
                        '.md', '.xml', '.json', '.xls', '.xlsx'
                    ]
                    if file_extension in supported_file_extensions:
                        request_type = "file"

        answer, sources = ragbot.chat_with_attachments(message.message, message.attachments)
        
        # Находим существующее сообщение пользователя и обновляем его тип
        user_message = db.query(Message).filter(
            Message.chat_id == message.chat_id,
            Message.content == message.message,
            Message.role == "user"
        ).first()
        
        if user_message:
            user_message.request_type = request_type
            db.commit()
        
        # Сохраняем ответ ассистента
        assistant_message = Message(
            chat_id=message.chat_id,
            role="assistant",
            content=answer,
            created_at=datetime.utcnow()
        )
        db.add(assistant_message)
        db.commit()
        
        formatted_sources = [
            {
                'source': source.metadata['source'].replace('/content/', '/data/'), 
                'page': source.metadata['page'], 
                'quote': source.page_content
            } 
            for source in sources
        ] if sources else None
        
        return RagbotResponse(text=answer, sources=formatted_sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload_file", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(default=None),
    url: str = Query(default=None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
):
    try:
        user = decode_access_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        upload_dir = "./uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = None
        file_type = None
        original_filename = None
        
        if file:
            file_extension = os.path.splitext(file.filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            file_type = "file"
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']:
                file_type = "image"
            elif file_extension in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']:
                file_type = "audio"
            elif file_extension in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                file_type = "video"
            elif file_extension in [
                '.txt', '.pdf', '.doc', '.docx', '.pptx', '.csv', '.html', '.htm',
                '.md', '.xml', '.json', '.xls', '.xlsx'
            ]:
                file_type = "file"
            
            original_filename = file.filename
        
        elif url:
            if not url.startswith(('http://', 'https://')):
                raise HTTPException(status_code=400, detail="Invalid URL format")
            file_path = url  
            file_type = "url"
            original_filename = url
        
        else:
            raise HTTPException(status_code=400, detail="Either file or URL must be provided")
        
        return FileUploadResponse(
            original_filename=original_filename,
            file_path=file_path,
            attachment_format=[(file_type, file_path)]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/categorize", response_model=CategoryResponse)
async def categorize_message(
    request: CategoryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
):
    try:
        user = decode_access_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        result = categorize_text(db, request.text, int(request.chat_id))
        
        # Получаем ID категорий из базы данных
        category_level_1 = db.query(Category).filter(
            Category.name == result["category_level_1"]
        ).first()
        
        category_level_2 = db.query(Category).filter(
            Category.name == result["category_level_2"]
        ).first()
        
        # Сохраняем сообщение пользователя с категориями
        user_message = Message(
            chat_id=int(request.chat_id),
            role="user",
            content=request.text,
            request_type="text",
            category_level_1_id=category_level_1.id if category_level_1 else None,
            category_level_2_id=category_level_2.id if category_level_2 else None,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        
        return CategoryResponse(
            category_level_1=result["category_level_1"],
            category_level_2=result["category_level_2"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))