from django.core.management.base import BaseCommand
from django.utils import timezone
from adminApp.models import User, Model, EmbeddingModel, ModelConfiguration, Chat, Message, Category
from faker import Faker
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generates test data for the application'

    def handle(self, *args, **kwargs):
        fake = Faker('ru_RU')
        
        # Создаем тестового пользователя, если его нет
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('test123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created test user'))

        # Создаем модели и конфигурации
        llm_model, _ = Model.objects.get_or_create(
            name='GPT-3.5-turbo',
            defaults={'temperature': 0.7}
        )
        
        embedding_model, _ = EmbeddingModel.objects.get_or_create(
            name='text-embedding-3-small'
        )
        
        config, _ = ModelConfiguration.objects.get_or_create(
            name='Default Configuration',
            defaults={
                'llm_model': llm_model,
                'embedding_model': embedding_model,
                'is_active': True
            }
        )

        # Типы запросов
        request_types = ['text', 'image', 'audio', 'document']

        # Получаем все категории первого уровня и их подкатегории
        categories = {}
        for cat in Category.objects.filter(parent=None):
            subcats = list(Category.objects.filter(parent=cat))
            if subcats:
                categories[cat] = subcats
            else:
                categories[cat] = [None]

        # Создаем чаты и сообщения
        chat_topics = [
            'Консультация по закупкам',
            'Вопросы по тендерам',
            'Помощь с документацией',
            'Техническая поддержка',
            'Общие вопросы'
        ]

        user_messages = [
            'Как правильно оформить заявку на участие в тендере?',
            'Какие документы нужны для участия в закупке?',
            'Можете объяснить процедуру электронного аукциона?',
            'Где найти информацию о текущих тендерах?',
            'Как рассчитать обеспечение заявки?',
            'Какие требования к участникам закупки?',
            'Можно ли изменить заявку после подачи?',
            'Как работает система электронных торгов?',
            'Что делать если возникли технические проблемы?',
            'Как подать жалобу на результаты тендера?'
        ]

        assistant_messages = [
            'Для оформления заявки необходимо следовать следующим шагам...',
            'Основной пакет документов включает в себя...',
            'Электронный аукцион проводится в следующем порядке...',
            'Информацию о текущих тендерах можно найти на площадках...',
            'Обеспечение заявки рассчитывается как процент от начальной цены...',
            'К участникам закупки предъявляются следующие требования...',
            'Изменение заявки возможно до окончания срока подачи...',
            'Электронные торги проводятся на специализированных площадках...',
            'При возникновении технических проблем необходимо...',
            'Порядок подачи жалобы регламентируется законом...'
        ]

        # Создаем 5 чатов
        for topic in chat_topics:
            chat = Chat.objects.create(
                user=user,
                title=topic,
                is_active=True
            )
            
            # В каждом чате создаем 10-15 пар сообщений
            num_pairs = random.randint(10, 15)
            base_time = timezone.now() - timedelta(days=30)
            
            for i in range(num_pairs):
                # Выбираем случайный тип запроса
                request_type = random.choice(request_types)
                
                # Выбираем случайную категорию и подкатегорию
                category_1 = random.choice(list(categories.keys()))
                category_2 = random.choice(categories[category_1])
                
                # Сообщение пользователя
                user_msg = Message.objects.create(
                    chat=chat,
                    role='user',
                    content=random.choice(user_messages),
                    created_at=base_time + timedelta(minutes=i*30),
                    configuration=config,
                    request_type=request_type,
                    category_level_1=category_1,
                    category_level_2=category_2
                )

                # Ответ ассистента
                assistant_msg = Message.objects.create(
                    chat=chat,
                    role='assistant',
                    content=random.choice(assistant_messages),
                    created_at=base_time + timedelta(minutes=i*30 + 1),
                    configuration=config,
                    request_type=request_type,
                    category_level_1=category_1,
                    category_level_2=category_2,
                    rating=random.randint(3, 5) if random.random() > 0.3 else None
                )

        self.stdout.write(self.style.SUCCESS('Successfully generated test data')) 