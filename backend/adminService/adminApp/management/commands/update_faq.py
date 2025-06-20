from django.core.management.base import BaseCommand
from adminApp.update_faq_answers import Command as UpdateCommand

class Command(BaseCommand):
    help = 'Обновляет ответы в FAQ'

    def handle(self, *args, **options):
        update_command = UpdateCommand()
        update_command.handle(*args, **options) 