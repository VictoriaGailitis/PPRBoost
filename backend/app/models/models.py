from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class SystemPrompt(Base):
    __tablename__ = 'system_prompts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    text = Column(Text)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    password = Column(String(128), nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_superuser = Column(Boolean, default=False)
    username = Column(String(150), unique=True, nullable=False)
    first_name = Column(String(150), default='')
    last_name = Column(String(150), default='')
    email = Column(String(254), unique=True)
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    date_joined = Column(DateTime, server_default=func.now())
    system_prompt_id = Column(Integer, ForeignKey('system_prompts.id'), nullable=True)

    system_prompt = relationship("SystemPrompt")
    chats = relationship("Chat", back_populates="user")

class Model(Base):
    __tablename__ = 'llm_models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    temperature = Column(Float, nullable=True, default=1.0)

class EmbeddingModel(Base):
    __tablename__ = 'embedding_models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

class ModelConfiguration(Base):
    __tablename__ = 'model_configurations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    llm_model_id = Column(Integer, ForeignKey('llm_models.id'))
    embedding_model_id = Column(Integer, ForeignKey('embedding_models.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    llm_model = relationship("Model")
    embedding_model = relationship("EmbeddingModel")

    __table_args__ = (
        UniqueConstraint('llm_model_id', 'embedding_model_id'),
    )

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)

    parent = relationship("Category", remote_side=[id])
    messages_level1 = relationship("Message", foreign_keys="Message.category_level_1_id", back_populates="category_level_1")
    messages_level2 = relationship("Message", foreign_keys="Message.category_level_2_id", back_populates="category_level_2")

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(200))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    role = Column(String(50))
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    configuration_id = Column(Integer, ForeignKey('model_configurations.id'), nullable=True)
    category_level_1_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    category_level_2_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    request_type = Column(String(100), nullable=True)
    rating = Column(Integer, nullable=True)

    chat = relationship("Chat", back_populates="messages")
    configuration = relationship("ModelConfiguration")
    category_level_1 = relationship("Category", foreign_keys=[category_level_1_id])
    category_level_2 = relationship("Category", foreign_keys=[category_level_2_id])
