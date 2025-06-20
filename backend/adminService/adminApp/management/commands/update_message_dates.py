from django.core.management.base import BaseCommand
from django.utils import timezone
import random
from datetime import timedelta
from adminApp.models import Message

class Command(BaseCommand):
    help = 'Обновляет даты создания сообщений на случайные даты за последние 12 месяцев'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=12,
            help='Количество месяцев для генерации дат (по умолчанию 12)'
        )

    def handle(self, *args, **options):
        months = options['months']
        
        # Получаем все сообщения
        messages = Message.objects.all()
        
        # Определяем диапазон дат
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30 * months)
        
        # Создаем список дат для каждого месяца
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date = current_date + timedelta(days=30)
        
        # Обновляем даты для каждого сообщения
        for message in messages:
            # Выбираем случайную дату из списка
            new_date = random.choice(dates)
            # Добавляем случайное количество дней (0-30) для разнообразия
            new_date = new_date + timedelta(days=random.randint(0, 30))
            # Добавляем случайное время в течение дня
            new_date = new_date.replace(
                hour=random.randint(0, 23),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            # Обновляем дату создания сообщения
            message.created_at = new_date
            message.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Обновлена дата для сообщения {message.id}: {new_date}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Успешно обновлены даты для {messages.count()} сообщений')
        ) 