from django.apps import AppConfig
from django.db.models.signals import post_migrate


class RecipesConfig(AppConfig):
    name = "recipes"

    def ready(self):
        from django.db.models.signals import post_migrate
        from .utils import load_initial_ingredients
        post_migrate.connect(load_initial_ingredients, sender=self)
