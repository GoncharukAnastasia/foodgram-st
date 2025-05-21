
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Импортирует ингредиенты из data/ingredients.json"

    def handle(self, *args, **options):
        file_path = Path(settings.BASE_DIR) / "data" / "ingredients.json"

        try:
            with file_path.open(encoding="utf-8") as fp:
                raw = json.load(fp)

            created = Ingredient.objects.bulk_create(
                (Ingredient(**item) for item in raw),
                ignore_conflicts=True,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Импорт завершён: добавлено {len(created)}, "
                    f"пропущено {len(raw) - len(created)}."
                )
            )

        except Exception as exc:
            raise CommandError(
                f"Импорт из «{file_path.name}» прерван: {exc}"
            ) from exc
