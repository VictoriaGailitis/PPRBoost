from django.core.management.base import BaseCommand
from adminApp.models import Model, EmbeddingModel, ModelConfiguration, Message
import random

class Command(BaseCommand):
    help = 'Генерирует конфигурации моделей и обновляет существующие записи'

    def handle(self, *args, **options):
        # Список популярных моделей с HuggingFace
        llm_models = [
            "meta-llama/Llama-2-7b-chat-hf",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "google/gemma-7b-it",
            "microsoft/phi-2",
            "Qwen/Qwen1.5-7B-Chat"
        ]

        embedding_models = [
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
            "intfloat/multilingual-e5-large",
            "BAAI/bge-large-en-v1.5",
            "WhereIsAI/UAE-Large-V1"
        ]

        # Создаем модели LLM
        for model_name in llm_models:
            Model.objects.get_or_create(
                name=model_name,
                defaults={
                    'temperature': 0.7
                }
            )

        # Создаем модели эмбеддингов
        for model_name in embedding_models:
            EmbeddingModel.objects.get_or_create(
                name=model_name
            )

        # Создаем конфигурации
        llm_models = list(Model.objects.all())
        embedding_models = list(EmbeddingModel.objects.all())

        for llm in llm_models:
            for embedding in embedding_models:
                ModelConfiguration.objects.get_or_create(
                    llm_model=llm,
                    embedding_model=embedding,
                    defaults={
                        'name': f'{llm.name} + {embedding.name}',
                        'is_active': True
                    }
                )

        # Обновляем существующие сообщения
        configurations = list(ModelConfiguration.objects.all())
        messages = Message.objects.all()

        for message in messages:
            if not message.configuration:
                # Назначаем случайную конфигурацию для сообщений без конфигурации
                message.configuration = random.choice(configurations)
                message.save()

        self.stdout.write(self.style.SUCCESS('Конфигурации успешно созданы и сообщения обновлены')) 