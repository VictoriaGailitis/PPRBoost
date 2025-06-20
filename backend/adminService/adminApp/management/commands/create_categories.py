from django.core.management.base import BaseCommand
from adminApp.models import Category

class Command(BaseCommand):
    help = 'Creates predefined categories'

    def handle(self, *args, **kwargs):
        categories_data = [
            (1, "_", None),
            (2, "_", 1),
            (3, "_", 1),
            (4, "_", None),
            (5, "_", 1),
            (6, "_", 1),
            (7, "_", None),
            (8, "_", 7),
            (9, "_", 7),
            (10, "_", 7),
            (11, "_", 7),
            (12, "_", 7),
            (13, "_", 7),
            (14, "_", 7),
            (15, "_", None),
            (16, "_", 15),
            (17, "_", 15),
            (18, "_", 15),
            (19, "_", 15),
            (20, "_", 15),
            (21, "_", 15),
            (22, "_", 15),
            (23, "_", None),
            (24, "_", 23),
            (25, "_", 23),
            (26, "_", 23),
            (27, "_", 23),
            (28, "_", 23),
            (29, "_", None),
            (30, "_", 29),
            (31, "_", 29),
            (32, "_", 29),
            (33, "_", 29),
            (34, "_", 29),
            (35, "_", None),
            (36, "_", 35),
            (37, "_", 35),
            (38, "_", 35),
            (39, "_", 35),
            (40, "_", 35),
            (41, "_", 35),
            (42, "_", 35),
            (43, "_", None),
            (44, "_", 43),
            (45, "_", 43),
            (46, "_", 43),
            (47, "_", 43),
            (48, "_", 43),
            (49, "_", None),
            (50, "_", 49),
            (51, "_", 49),
            (52, "_", 49),
            (53, "_", 49),
            (54, "_", None),
            (55, "_", 54),
            (56, "_", 54),
            (57, "_", None),
            (58, "_", 57),
            (59, "_", 57),
            (60, "_", 57),
            (61, "UNKNOWN - неопределенный класс", None),
        ]

        # Сначала создаем категории верхнего уровня
        for cat_id, name, parent_id in categories_data:
            if parent_id is None:
                Category.objects.get_or_create(
                    id=cat_id,
                    defaults={
                        'name': name,
                        'parent': None
                    }
                )

        # Затем создаем подкатегории
        for cat_id, name, parent_id in categories_data:
            if parent_id is not None:
                parent = Category.objects.get(id=parent_id)
                Category.objects.get_or_create(
                    id=cat_id,
                    defaults={
                        'name': name,
                        'parent': parent
                    }
                )

        self.stdout.write(self.style.SUCCESS('Successfully created categories')) 