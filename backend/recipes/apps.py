from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Конфигурация приложения recipes без 
    автоимпорта utils.load_initial_ingredients."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
