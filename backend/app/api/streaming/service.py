import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session, joinedload
from .categorizer_vllm import classify_text
from models.models import Category, Message, Chat, SystemPrompt, User, ModelConfiguration, Model, EmbeddingModel
from datetime import datetime

load_dotenv()

HUGGINGFACE_LLM_MODEL_LIST = os.getenv('HUGGINGFACE_LLM_MODEL_LIST')
HUGGINGFACE_LLM_MODEL_LIST_REASONING = os.getenv('HUGGINGFACE_LLM_MODEL_LIST_REASONING')

# Маппинг категорий из категоризатора в ID базы данных
CATEGORY_MAPPING = {
    "CAT_001": 1,  #
    "CAT_002": 2,  #
    "CAT_003": 3, #
    "CAT_004": 4, #
    "CAT_005": 5, #
    "CAT_006": 6, #
    "CAT_007": 7, #
    "CAT_008": 8, #
    "CAT_009": 9, #
    "CAT_010": 10, #
    "CAT_011": 11  # UNKNOWN - неопределенный класс
}

SUBCATEGORY_MAPPING = {
    # Подкатегории для CAT_001
    "SUB_001_01": 12,  #
    "SUB_001_02": 13,  #
    "SUB_001_03": 14,  #
    "SUB_001_04": 15,  #
    "SUB_001_05": 16,  #

    # Подкатегории для CAT_002
    "SUB_002_01": 17,  #
    "SUB_002_02": 18,  #
    "SUB_002_03": 19, #
    "SUB_002_04": 20, #
    "SUB_002_05": 21, #
    "SUB_002_06": 22, #
    "SUB_002_07": 23, #

    # Подкатегории для CAT_003
    "SUB_003_01": 24, #
    "SUB_003_02": 25, #
    "SUB_003_03": 26, #
    "SUB_003_04": 27, #
    "SUB_003_05": 28, #
    "SUB_003_06": 29, #
    "SUB_003_07": 30, #

    # Подкатегории для CAT_004
    "SUB_004_01": 31, #
    "SUB_004_02": 32, #
    "SUB_004_03": 33, #
    "SUB_004_04": 34, #
    "SUB_004_05": 35, #

    # Подкатегории для CAT_005
    "SUB_005_01": 36, #
    "SUB_005_02": 37, #
    "SUB_005_03": 38, #
    "SUB_005_04": 39, #
    "SUB_005_05": 40, #

    # Подкатегории для CAT_006
    "SUB_006_01": 41, #
    "SUB_006_02": 42, #
    "SUB_006_03": 43, #
    "SUB_006_04": 44, #
    "SUB_006_05": 45, #
    "SUB_006_06": 46, #
    "SUB_006_07": 47, #

    # Подкатегории для CAT_007
    "SUB_007_01": 48, #
    "SUB_007_02": 49, #
    "SUB_007_03": 50, #
    "SUB_007_04": 51, #
    "SUB_007_05": 52, #

    # Подкатегории для CAT_008
    "SUB_008_01": 53, #
    "SUB_008_02": 54, #
    "SUB_008_03": 55, #
    "SUB_008_04": 56, #

    # Подкатегории для CAT_009
    "SUB_009_01": 57, #
    "SUB_009_02": 58, #

    # Подкатегории для CAT_010
    "SUB_010_01": 59, #
    "SUB_010_02": 60, #
    "SUB_010_03": 61  #
}

def save_user_message(
    db: Session,
    chat_id: int,
    content: str,
    category_1_id: int = None,
    category_2_id: int = None
) -> Message:
    # Создаем сообщение
    message = Message(
        chat_id=chat_id,
        role="user",
        content=content,
        category_level_1_id=category_1_id,
        category_level_2_id=category_2_id,
        created_at=datetime.now()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def categorize_text(db: Session, text: str, chat_id: int = None) -> dict:
    # Получаем категории из классификатора
    cat_1_id, cat_2_id = classify_text(text)
    
    # Получаем ID категорий из базы данных
    db_cat_1_id = CATEGORY_MAPPING.get(cat_1_id)
    
    # Получаем категорию первого уровня из базы данных
    category_1 = db.query(Category).filter(Category.id == db_cat_1_id).first() if db_cat_1_id else None
    
    # Если это UNKNOWN категория, возвращаем только её
    if cat_1_id == "CAT_011":
        # Сохраняем сообщение, если предоставлен chat_id
        if chat_id:
            save_user_message(
                db,
                chat_id=chat_id,
                content=text,
                category_1_id=category_1.id if category_1 else None
            )
        return {
            "category_level_1": category_1.name if category_1 else None,
            "category_level_2": None
        }
    
    # Для остальных категорий получаем подкатегорию
    db_cat_2_id = SUBCATEGORY_MAPPING.get(cat_2_id) if cat_2_id else None
    category_2 = db.query(Category).filter(Category.id == db_cat_2_id).first() if db_cat_2_id else None
    
    # Сохраняем сообщение, если предоставлен chat_id
    if chat_id:
        save_user_message(
            db,
            chat_id=chat_id,
            content=text,
            category_1_id=category_1.id if category_1 else None,
            category_2_id=category_2.id if category_2 else None
        )
    
    return {
        "category_level_1": category_1.name if category_1 else None,
        "category_level_2": category_2.name if category_2 else None
    }

async def get_system_prompt(db: Session, prompt_id: int) -> str:
    """Получает текст системного промпта из базы данных по его ID."""
    prompt = db.query(SystemPrompt).filter(SystemPrompt.id == prompt_id).first()
    if not prompt:
        return None
    return prompt.text 

async def get_user_system_prompt(db: Session, user_id: int) -> str:
    """Получает текст системного промпта пользователя из базы данных."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.system_prompt_id:
        return None
    
    prompt = db.query(SystemPrompt).filter(SystemPrompt.id == user.system_prompt_id).first()
    return prompt.text if prompt else None 

def get_active_configuration(db: Session) -> tuple[str, str]:
    """
    Получает первую активную конфигурацию моделей из базы данных,
    где имя LLM модели соответствует списку HUGGINGFACE_LLM_MODEL_LIST.
    Использует JOIN для получения связанных моделей llm и embedding.
    """

    if not HUGGINGFACE_LLM_MODEL_LIST:
        raise ValueError("HUGGINGFACE_LLM_MODEL_LIST is not defined in environment variables")
    
    model_list = HUGGINGFACE_LLM_MODEL_LIST.split(',')

    config = (db.query(ModelConfiguration)
             .join(Model, ModelConfiguration.llm_model_id == Model.id)
             .join(EmbeddingModel, ModelConfiguration.embedding_model_id == EmbeddingModel.id)
             .filter(
                 ModelConfiguration.is_active == True,
                 Model.name.in_(model_list)
             )
             .options(
                 joinedload(ModelConfiguration.llm_model),
                 joinedload(ModelConfiguration.embedding_model)
             )
             .first())
    
    if not config:
        # Если не нашли конфигурацию из списка, берем первую активную
        config = (db.query(ModelConfiguration)
                 .join(Model, ModelConfiguration.llm_model_id == Model.id)
                 .join(EmbeddingModel, ModelConfiguration.embedding_model_id == EmbeddingModel.id)
                 .filter(ModelConfiguration.is_active == True)
                 .options(
                     joinedload(ModelConfiguration.llm_model),
                     joinedload(ModelConfiguration.embedding_model)
                 )
                 .first())
        
        if not config:
            raise ValueError("No active model configuration found")
    
    return config.llm_model.name, config.embedding_model.name

def get_active_thinking_configuration(db: Session) -> tuple[str, str]:
    """
    Получает первую активную конфигурацию для режима thinking из базы данных,
    где имя LLM модели соответствует списку HUGGINGFACE_LLM_MODEL_LIST_REASONING.
    Использует JOIN для получения связанных моделей llm и embedding.
    """
    if not HUGGINGFACE_LLM_MODEL_LIST_REASONING:
        raise ValueError("HUGGINGFACE_LLM_MODEL_LIST_REASONING is not defined in environment variables")
    
    model_list = HUGGINGFACE_LLM_MODEL_LIST_REASONING.split(',')
    
    config = (db.query(ModelConfiguration)
             .join(Model, ModelConfiguration.llm_model_id == Model.id)
             .join(EmbeddingModel, ModelConfiguration.embedding_model_id == EmbeddingModel.id)
             .filter(
                 ModelConfiguration.is_active == True,
                 Model.name.in_(model_list)
             )
             .options(
                 joinedload(ModelConfiguration.llm_model),
                 joinedload(ModelConfiguration.embedding_model)
             )
             .first())
    
    if not config:
        raise ValueError("No active thinking model configuration found with specified LLM models")
    
    return config.llm_model.name, config.embedding_model.name