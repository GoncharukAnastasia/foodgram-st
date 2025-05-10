import json
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загружает ингредиенты из data/ingredients.json."""
    help = 'Импортирует ингредиенты из data/ingredients.json'

    def handle(self, *args, **options):
        file_path = Path(__file__).resolve(
        ).parents[5] / 'data/ingredients.json'
        with open(file_path, encoding='utf-8') as file:
            data = json.load(file)

        created, skipped = 0, 0
        for item in data:
            obj, is_created = Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit'],
            )
            created += is_created
            skipped += not is_created

        self.stdout.write(
            self.style.SUCCESS(
                f'Добавлено: {created}, пропущено (уже есть): {skipped}'
            )
        )
