
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from rest_framework.views import APIView

from recipes.models import Recipe


class RecipeRedirectView(APIView):
    """
    Проверяем, что рецепт существует — `404`, если нет.
    Перенаправляем на «правильный» URL карточки рецепта.
    """

    authentication_classes: list = []       # доступен всем
    permission_classes: list = []

    def get(self, request, pk: int | str):
        get_object_or_404(Recipe, pk=pk)

        return redirect(reverse("recipe-detail", args=[pk]))
