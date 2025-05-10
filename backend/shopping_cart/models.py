from django.conf import settings
from django.db import models

from recipes.models import Recipe

User = settings.AUTH_USER_MODEL


class ShoppingCart(models.Model):
    """Какие рецепты пользователь хочет купить."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='cart'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='in_carts'
    )
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Покупка'
        verbose_name_plural = 'Список покупок'

    def __str__(self) -> str:
        return f'{self.user} {self.recipe}'
