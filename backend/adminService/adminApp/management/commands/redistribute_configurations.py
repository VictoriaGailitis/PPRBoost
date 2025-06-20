from django.core.management.base import BaseCommand
from adminApp.models import ModelConfiguration, Message
from django.db.models import Count
import random
from collections import defaultdict

class Command(BaseCommand):
    help = 'Перераспределяет конфигурации моделей между сообщениями для создания более полного датасета'

    def handle(self, *args, **options):
        # Получаем все конфигурации и сообщения
        configurations = list(ModelConfiguration.objects.all())
        messages = Message.objects.all()
        
        if not configurations:
            self.stdout.write(self.style.ERROR('Нет доступных конфигураций'))
            return
            
        if not messages:
            self.stdout.write(self.style.ERROR('Нет сообщений для обновления'))
            return

        # Считаем текущее распределение конфигураций
        current_distribution = defaultdict(int)
        for message in messages:
            if message.configuration:
                current_distribution[message.configuration.id] += 1

        # Вычисляем целевое количество сообщений на конфигурацию
        target_per_config = len(messages) // len(configurations)
        remaining = len(messages) % len(configurations)

        # Создаем список конфигураций с учетом целевого распределения
        config_pool = []
        for config in configurations:
            # Добавляем базовое количество
            config_pool.extend([config] * target_per_config)
            # Добавляем оставшиеся сообщения по одной на конфигурацию
            if remaining > 0:
                config_pool.append(config)
                remaining -= 1

        # Перемешиваем пул конфигураций
        random.shuffle(config_pool)

        # Обновляем конфигурации для сообщений
        for i, message in enumerate(messages):
            if i < len(config_pool):
                message.configuration = config_pool[i]
                message.save()

        # Выводим статистику
        new_distribution = defaultdict(int)
        for message in messages:
            if message.configuration:
                new_distribution[message.configuration.name] += 1

        self.stdout.write(self.style.SUCCESS('Статистика распределения конфигураций:'))
        for config_name, count in new_distribution.items():
            self.stdout.write(f'{config_name}: {count} сообщений')

        self.stdout.write(self.style.SUCCESS('Конфигурации успешно перераспределены')) 