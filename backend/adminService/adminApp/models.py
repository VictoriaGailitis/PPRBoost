from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class SystemPrompt(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название промпта")
    text = models.TextField(verbose_name="Текст промпта")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Системный промпт"
        verbose_name_plural = "Системные промпты"
        db_table = 'system_prompts'

class User(AbstractUser):
    system_prompt = models.ForeignKey(SystemPrompt, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Системный промпт', db_column='system_prompt_id')
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'users'

class Model(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название модели')
    temperature = models.FloatField(null=True, default=1.0, verbose_name='Температура')
    
    class Meta:
        verbose_name = 'Модель'
        verbose_name_plural = 'Модели'
        db_table = 'llm_models'
    
    def __str__(self):
        return self.name

class EmbeddingModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название модели')
    
    class Meta:
        verbose_name = 'Модель эмбеддингов'
        verbose_name_plural = 'Модели эмбеддингов'
        db_table = 'embedding_models'
    
    def __str__(self):
        return self.name

class ModelConfiguration(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название конфигурации')
    llm_model = models.ForeignKey(Model, on_delete=models.CASCADE, verbose_name='LLM модель', db_column='llm_model_id')
    embedding_model = models.ForeignKey(EmbeddingModel, on_delete=models.CASCADE, verbose_name='Модель эмбеддингов', db_column='embedding_model_id')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Конфигурация моделей'
        verbose_name_plural = 'Конфигурации моделей'
        db_table = 'model_configurations'
        unique_together = ['llm_model', 'embedding_model']

    def __str__(self):
        return f"{self.name} ({self.llm_model.name} + {self.embedding_model.name})"

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название категории')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, db_column='parent_id')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        db_table = 'categories'
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats', db_column='user_id')
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        db_table = 'chats'
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages', db_column='chat_id')
    role = models.CharField(max_length=50)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    configuration = models.ForeignKey(ModelConfiguration, on_delete=models.SET_NULL, null=True, verbose_name='Конфигурация моделей', db_column='configuration_id')
    category_level_1 = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, 
                                       verbose_name='Категория 1-го уровня', 
                                       related_name='messages_level1',
                                       db_column='category_level_1_id',
                                       limit_choices_to={'parent': None})
    category_level_2 = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, 
                                       verbose_name='Категория 2-го уровня',
                                       related_name='messages_level2',
                                       db_column='category_level_2_id')
    request_type = models.CharField(max_length=100, null=True, blank=True, verbose_name='Тип запроса')
    rating = models.IntegerField(null=True, blank=True, verbose_name='Оценка',
                               help_text='Оценка ответа от 1 до 5',
                               validators=[
                                   MinValueValidator(1),
                                   MaxValueValidator(5)
                               ])
    
    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        db_table = 'messages'
        ordering = ['created_at']

class FinetuneTimer(models.Model):
    is_running = models.BooleanField(default=False, verbose_name='Таймер запущен')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='Время начала')
    duration_hours = models.FloatField(null=True, blank=True, verbose_name='Длительность (часы)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Таймер finetune'
        verbose_name_plural = 'Таймеры finetune'

    def __str__(self):
        return f"Finetune Timer ({'running' if self.is_running else 'stopped'})"
