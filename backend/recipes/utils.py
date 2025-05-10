# recipes/utils.py
import json
from pathlib import Path
from django.conf import settings
from recipes.models import Ingredient


def load_initial_ingredients(sender, **kwargs):
    from recipes.models import Ingredient          # импорт внутрь функции
    if Ingredient.objects.exists():
        return

    data_file = Path(settings.BASE_DIR) / 'data' / 'ingredients.json'
    with open(data_file, encoding='utf-8') as f:
        items = json.load(f)

    Ingredient.objects.bulk_create(
        Ingredient(**item) for item in items
    )
