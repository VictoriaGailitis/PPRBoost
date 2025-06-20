import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session, joinedload
from ml.categorizer_vllm import classify_text
from models.models import Category, Message, Chat, SystemPrompt, User, ModelConfiguration, Model, EmbeddingModel
from datetime import datetime

load_dotenv()

HUGGINGFACE_LLM_MODEL_LIST = os.getenv('HUGGINGFACE_LLM_MODEL_LIST')
HUGGINGFACE_LLM_MODEL_LIST_REASONING = os.getenv('HUGGINGFACE_LLM_MODEL_LIST_REASONING')

# Маппинг категорий из категоризатора в ID базы данных
CATEGORY_MAPPING = {
    "CAT_001": 1,    # Как начать работу
    "CAT_002": 2,    # Заправка
    "CAT_003": 3,    # Ремонт и обслуживание
    "CAT_004": 4,    # Дорожные платежи
    "CAT_005": 5,    # Страхование
    "CAT_006": 6,    # Маркетплейс
    "CAT_007": 7,    # Управление автопарком
    "CAT_008": 8,    # Сервисы для бизнеса
    "CAT_009": 9,    # Финансовые сервисы
    "CAT_010": 10,   # Цифровые сервисы
    "CAT_011": 11,   # Интерфейсы
    "CAT_012": 62,   # Инструкции
    "CAT_013": 63,   # Реферальная программа Рекомендация
    "CAT_014": 64,   # UNKNOWN - неопределенный класс
}

SUBCATEGORY_MAPPING = {
    # CAT_001: Как начать работу
    "SUB_001_01": 12,  # Виртуальные карты
    "SUB_001_02": 13,  # Добавление сотрудников и авто в Личный Кабинет
    "SUB_001_03": 14,  # Инструкции по работе с Личным Кабинетом
    "SUB_001_04": 15,  # Начало работы в мобильном приложении ППР
    # CAT_002: Заправка
    "SUB_002_01": 17,  # Топливо
    "SUB_002_02": 18,  # Электрозарядки
    "SUB_002_03": 19,  # Товары на АЗС
    "SUB_002_04": 20,  # Доставка топлива
    # CAT_003: Ремонт и обслуживание
    "SUB_003_01": 24,  # Мойки
    "SUB_003_02": 25,  # Шиномонтаж
    "SUB_003_03": 26,  # Ремонт и ТО
    "SUB_003_04": 27,  # Хранение шин и дисков
    "SUB_003_05": 28,  # Выездной шиномонтаж
    "SUB_003_06": 29,  # Заправка автомобильных кондиционеров
    # CAT_004: Дорожные платежи
    "SUB_004_01": 31,  # Штрафы
    "SUB_004_02": 32,  # Парковки
    "SUB_004_03": 33,  # Платные дороги
    "SUB_004_04": 34,  # Помощь на дорогах
    "SUB_004_05": 35,  # Эвакуаторы
    # CAT_005: Страхование
    "SUB_005_01": 36,  # Страхование авто
    "SUB_005_02": 37,  # КАСКО с топливом
    "SUB_005_03": 38,  # Страхование грузов
    "SUB_005_04": 39,  # Страхование ответственности
    # CAT_006: Маркетплейс
    "SUB_006_01": 41,  # Покупка шин и дисков
    "SUB_006_02": 42,  # Запчасти
    # CAT_007: Управление автопарком
    "SUB_007_01": 48,  # Модуль управление автопарком
    "SUB_007_02": 49,  # Электронные путевые листы
    # CAT_008: Сервисы для бизнеса
    "SUB_008_01": 53,  # Такси, доставка, еда и товары
    "SUB_008_02": 54,  # Каршеринг
    "SUB_008_03": 55,  # Командировки
    "SUB_008_04": 56,  # Трансферы
    # CAT_009: Финансовые сервисы
    "SUB_009_01": 57,  # Лизинг
    "SUB_009_02": 58,  # Отсрочка платежа
    # CAT_010: Цифровые сервисы
    "SUB_010_01": 59,  # API
    # CAT_011: Интерфейсы
    "SUB_011_01": 65,  # Личный кабинет
    "SUB_011_02": 66,  # Мобильное приложение
    "SUB_011_03": 67,  # Чат-бот
    "SUB_011_04": 68,  # Гараж
    # CAT_012: Инструкции
    "SUB_012_01": 69,  # Правила оплаты
    # CAT_013: Реферальная программа Рекомендация
    "SUB_013_01": 70,  # О программе Рекомендация
    "SUB_013_02": 71,  # Как принять участие
    "SUB_013_03": 72,  # Как воспользоваться бонусами Benzuber
}

THIRD_LEVEL_CATEGORY_MAPPING = {
    # SUB_002_01: Топливо
    "SUB_002_01_01": 73,  # Что такое топливная карта
    "SUB_001_01_02": 74,  # Как топливная карта упрощает бизнес
    "SUB_001_01_03": 75,  # Выбор топливной карты
    "SUB_001_01_04": 76,  # Управление топливной картой
    "SUB_001_01_05": 77,  # Сеть приема топливных карт
    # SUB_002_02: Электрозарядки
    "SUB_002_02_01": 78,  # О сервисе Электрозарядки
    "SUB_002_02_02": 79,  # Как подключить Электрозарядки
    "SUB_002_02_03": 80,  # Сеть приема Электрозарядок
    # SUB_002_03: Товары на АЗС
    "SUB_002_03_01": 81,  # О сервисе Товары на АЗС
    "SUB_002_03_02": 82,  # Как подключить Товары на АЗС
    "SUB_002_03_03": 83,  # Сеть приема Товаров на АЗС
    "SUB_002_03_04": 84,  # Акции на товары на АЗС
    # SUB_002_04: Доставка топлива
    "SUB_002_04_01": 85,  # О сервисе Доставка топлива
    "SUB_002_04_02": 86,  # Как подключить Доставку топлива
    "SUB_002_04_03": 87,  # Управление заказом доставки топлива
    "SUB_002_04_04": 88,  # Доставка топлива: большой объем
    # SUB_003_01: Мойки
    "SUB_003_01_01": 89,  # О сервисе Мойка
    "SUB_003_01_02": 90,  # Как подключить Мойки
    "SUB_003_01_03": 91,  # Сеть приема Моек
    "SUB_003_01_04": 92,  # Оплата мойки через PPR Pay
    # SUB_003_02: Шиномонтаж
    "SUB_003_02_01": 93,  # О сервисе Шиномонтаж
    "SUB_003_02_02": 94,  # Как подключить Шиномонтаж
    "SUB_003_02_03": 95,  # Сеть приема Шиномонтажа
    # SUB_003_03: Ремонт и ТО
    "SUB_003_03_01": 96,  # О сервисе Ремонт и ТО
    "SUB_003_03_02": 97,  # Как подключить Ремонт и ТО
    # SUB_003_04: Хранение шин и дисков
    "SUB_003_04_01": 98,  # О сервисе Хранение шин и дисков
    "SUB_003_04_02": 99,  # Как подключить Хранение шин и дисков
    "SUB_003_04_03": 100, # Адреса складов для хранения шин и дисков
    "SUB_003_04_04": 101, # Стоимость хранения шин и дисков
    # SUB_003_05: Выездной шиномонтаж
    "SUB_003_05_01": 102, # О сервисе Выездной шиномонтаж
    "SUB_003_05_02": 103, # Как подключить Выездной шиномонтаж
    "SUB_003_05_03": 104, # Стоимость Выездного шиномонтажа
    # SUB_003_06: Заправка автомобильных кондиционеров
    "SUB_003_06_01": 105, # О сервисе Заправка автомобильных кондиционеров
    "SUB_003_06_02": 106, # Как подключить Заправку автомобильных кондиционеров
    # SUB_004_01: Штрафы
    "SUB_004_01_01": 107, # О сервисе Штрафы
    "SUB_004_01_02": 108, # Мониторинг штрафов
    "SUB_004_01_03": 109, # Оплата штрафов
    "SUB_004_01_04": 110, # Обжалование штрафов
    # SUB_004_02: Парковки
    "SUB_004_02_01": 111, # О сервисе Парковки
    "SUB_004_02_02": 112, # Как подключить Парковки
    "SUB_004_02_03": 113, # Парковочная сессия
    # SUB_004_03: Платные дороги
    "SUB_004_03_01": 114, # О сервисе Платные дороги
    "SUB_004_03_02": 115, # Транспондеры
    "SUB_004_03_03": 116, # Стоимость проезда
    # SUB_004_04: Помощь на дорогах
    "SUB_004_04_01": 117, # О сервисе Помощь на дорогах
    "SUB_004_04_02": 118, # Как подключить Помощь на дорогах
    # SUB_004_05: Эвакуаторы
    "SUB_004_05_01": 119, # О сервисе Эвакуаторы
    "SUB_004_05_02": 120, # Как подключить Эвакуаторы
    "SUB_004_05_03": 121, # Как вызвать Эвакуатор в Мобильном приложении
    # SUB_005_01: Страхование авто
    "SUB_005_01_01": 122, # Страхование ОСАГО
    "SUB_005_01_02": 123, # Страхование КАСКО
    # SUB_005_02: КАСКО с топливом
    "SUB_005_02_01": 124, # О сервисе Каско с топливом
    "SUB_005_02_02": 125, # Как подключить Каско с топливом
    # SUB_005_03: Страхование грузов
    "SUB_005_03_01": 126, # О сервисе Страхование грузов
    "SUB_005_03_02": 127, # Как подключить Страхование грузов
    # SUB_005_04: Страхование ответственности
    "SUB_005_04_01": 128, # Отличие перевозчика от экспедитора
    "SUB_005_04_02": 129, # Что страхуем по услуге ответственность перевозчика и экспедитора
    "SUB_005_04_03": 130, # Страхование ответственности перевозчика
    "SUB_005_04_04": 131, # Страхование ответственности экспедитора
    # SUB_006_01: Покупка шин и дисков
    "SUB_006_01_01": 132, # О сервисе Шины и диски
    "SUB_006_01_02": 133, # Как подключить Шины и диски
    "SUB_006_01_03": 134, # Доставка шин и дисков
    # SUB_006_02: Запчасти
    "SUB_006_02_01": 135, # О сервисе Запчасти
    "SUB_006_02_02": 136, # Как подключить Запчасти
    # SUB_007_01: Модуль управление автопарком
    "SUB_007_01_01": 137, # О сервисе Управление автопарком
    "SUB_007_01_02": 138, # Как подключить Управление автопарком
    # SUB_007_02: Электронные путевые листы
    "SUB_007_02_01": 139, # О сервисе ЭПЛ
    "SUB_007_02_02": 140, # Как подключить ЭПЛ
    # SUB_008_01: Такси, доставка, еда и товары
    "SUB_008_01_01": 141, # О сервисе Такси, доставка, еда и товары
    "SUB_008_01_02": 142, # Инструкции по подключению и использованию сервиса Такси, доставка, еда и товары
    "SUB_008_01_03": 143, # Инструкция по использованию мобильного приложения Яндекс Go
    "SUB_008_01_04": 144, # Инструкция по использованию мобильного приложения Bibi
    "SUB_008_01_05": 145, # Инструкция по использованию мобильного приложения SwiftDrive
    # SUB_008_02: Каршеринг
    "SUB_008_02_01": 146, # О сервисе Каршеринг
    "SUB_008_02_02": 147, # Как подключить Каршеринг
    "SUB_008_02_03": 148, # Инструкция по использованию BelkaCar
    "SUB_008_02_04": 149, # Инструкция по использованию Яндекс Драйв
    # SUB_008_03: Командировки
    "SUB_008_03_01": 150, # О сервисе Командировки
    "SUB_008_03_02": 151, # Как подключить Командировки
    "SUB_008_03_03": 152, # Управление Командировками
    # SUB_008_04: Трансферы
    "SUB_008_04_01": 153, # О сервисе Трансферы
    "SUB_008_04_02": 154, # Как подключить Трансферы
    "SUB_008_04_03": 155, # Инструкция по работе в личном кабинете IWAY
    # SUB_009_01: Лизинг
    "SUB_009_01_01": 156, # О сервисе Лизинг
    "SUB_009_01_02": 157, # Как подключить Лизинг
    "SUB_009_01_03": 158, # Партнеры по лизингу
    # SUB_009_02: Отсрочка платежа
    "SUB_009_02_01": 159, # Недельное Кредитование
    "SUB_009_02_02": 160, # Двухнедельное кредитование
    # SUB_010_01: API
    "SUB_010_01_01": 161, # О сервисе API на чтение
    "SUB_010_01_02": 162, # Как подключить и начать использовать API на чтение
    "SUB_010_01_03": 163, # Стоимость услуги API на чтение
    # SUB_011_01: Личный кабинет
    "SUB_011_01_01": 164, # О Личном кабинете
    "SUB_011_01_02": 165, # Доступ в личный кабинет
    "SUB_011_01_03": 166, # Группа компаний
    "SUB_011_01_04": 167, # Настройки компании
    "SUB_011_01_05": 168, # Заказ и активация карт
    "SUB_011_01_06": 169, # Раздел Карты
    "SUB_011_01_07": 170, # Раздел Транзакции
    "SUB_011_01_08": 171, # Раздел Отчеты и графики
    "SUB_011_01_09": 172, # Раздел Документы
    "SUB_011_01_10": 173, # Раздел Услуги
    "SUB_011_01_11": 174, # Раздел Сеть приема
    "SUB_011_01_12": 175, # Раздел Заявки
    "SUB_011_01_13": 176, # Раздел Штрафы
    # SUB_011_02: Мобильное приложение
    "SUB_011_02_01": 177, # Начало работы в мобильном приложении
    "SUB_011_02_02": 178, # Доступ в мобильное приложение
    "SUB_011_02_03": 179, # PPR Pay
    "SUB_011_02_04": 180, # Система Быстрых Платежей
    "SUB_011_02_05": 181, # Оплата кофе на АЗС из приложения
    "SUB_011_02_06": 182, # Сбербизнес
    # SUB_011_03: Чат-бот
    "SUB_011_03_01": 183, # Доступ в чат-бот
    # SUB_011_04: Гараж
    "SUB_011_04_01": 184, # О сервисе Гараж
    "SUB_011_04_02": 185, # Как работать с разделом Гараж
    # SUB_012_01: Правила оплаты
    "SUB_012_01_01": 186, # Счет-фактура
    "SUB_012_01_02": 187, # График зачисления платежей
}

def save_user_message(
    db: Session,
    chat_id: int,
    content: str,
    category_1_id: int = None,
    category_2_id: int = None,
    category_3_id: int = None
) -> Message:
    # Создаем сообщение
    message = Message(
        chat_id=chat_id,
        role="user",
        content=content,
        category_level_1_id=category_1_id,
        category_level_2_id=category_2_id,
        category_level_3_id=category_3_id,
        created_at=datetime.now()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def categorize_text(db: Session, text: str, chat_id: int = None) -> dict:
    # Получаем категории из классификатора
    cat_1_id, cat_2_id, cat_3_id = classify_text(text)
    
    # Получаем ID категорий из базы данных
    db_cat_1_id = CATEGORY_MAPPING.get(cat_1_id)
    
    # Получаем категорию первого уровня из базы данных
    category_1 = db.query(Category).filter(Category.id == db_cat_1_id).first() if db_cat_1_id else None
    
    # Если это UNKNOWN категория, возвращаем только её
    if cat_1_id == "CAT_014":
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
            "category_level_2": None,
            "category_level_3": None
        }
    
    # Для остальных категорий получаем подкатегорию
    db_cat_2_id = SUBCATEGORY_MAPPING.get(cat_2_id) if cat_2_id else None
    category_2 = db.query(Category).filter(Category.id == db_cat_2_id).first() if db_cat_2_id else None

    db_cat_3_id = THIRD_LEVEL_CATEGORY_MAPPING.get(cat_3_id) if cat_3_id else None
    category_3 = db.query(Category).filter(Category.id == db_cat_3_id).first() if db_cat_3_id else None
    
    # Сохраняем сообщение, если предоставлен chat_id
    if chat_id:
        save_user_message(
            db,
            chat_id=chat_id,
            content=text,
            category_1_id=category_1.id if category_1 else None,
            category_2_id=category_2.id if category_2 else None,
            category_3_id=category_3.id if category_3 else None
        )
    
    return {
        "category_level_1": category_1.name if category_1 else None,
        "category_level_2": category_2.name if category_2 else None,
        "category_level_3": category_3.name if category_3 else None
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