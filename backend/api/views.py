from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, Favorite, ShoppingCart
from users.models import Follow
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    AuthorCardSerializer,
)
User = get_user_model()

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        name = self.request.query_params.get('name')
        return qs.filter(name__istartswith=name) if name else qs


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (Recipe.objects
                .select_related('author')
                .prefetch_related('recipe_ingredients__ingredient'))
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)

    # сериализаторы
    def get_serializer_class(self):
        return (RecipeWriteSerializer
                if self.request.method in {'POST', 'PUT', 'PATCH'}
                else RecipeReadSerializer)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # helpers
    def _short_response(self, recipe, code):
        data = RecipeShortSerializer(
            recipe, context={'request': self.request}).data
        return Response(data, status=code)

    def _toggle_relation(self, model, recipe):
        request = self.request
        if request.method == 'POST':
            obj, created = model.objects.get_or_create(
                user=request.user, recipe=recipe)
            if not created:
                raise ValidationError('Рецепт уже добавлен')
            return self._short_response(recipe, status.HTTP_201_CREATED)

        # DELETE
        obj = model.objects.filter(
            user=self.request.user, recipe=recipe).first()
        if not obj:
            raise ValidationError({'errors': 'Этого рецепта нет в списке'})
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # избранное / корзина
    @action(detail=True, methods=('post', 'delete'),
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self._toggle_relation(Favorite, self.get_object())

    @action(detail=True, methods=('post', 'delete'), url_path='shopping_cart',
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self._toggle_relation(ShoppingCart, self.get_object())

    # фильтрация
    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        author = params.get('author')
        if author:
            qs = qs.filter(author_id=author)

        user = self.request.user
        if user.is_authenticated:
            if params.get('is_favorited') == '1':
                qs = qs.filter(favorites__user=user)
            if params.get('is_in_shopping_cart') == '1':
                qs = qs.filter(in_carts__user=user)
        return qs

    # короткая ссылка
    @action(detail=True, methods=('get',), url_path='get-link')
    def get_link(self, request, pk=None):
        url = request.build_absolute_uri(
            reverse('recipe-link', args=[pk])
        )
        return Response({'short-link': url})

    # скачать список покупок
    @action(detail=False, methods=('get',), url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        # Сначала достаём продукты с суммарными количествами
        products = (
            Ingredient.objects
            .filter(ingredient_recipes__recipe__in_carts__user=request.user)
            .values('name', 'measurement_unit')
            .annotate(total=Sum('ingredient_recipes__amount'))
            .order_by('name')
        )

        # А потом сам отчёт в одну строчку
        report = ('\n'.join([
            f"Список покупок для {request.user.username} — "
            f"{datetime.today().isoformat()} {datetime.now().strftime('%H:%M:%S')}",
            'Продукты:',
            *(
                f'{i}. {item["name"].title()} '
                f'({item["measurement_unit"]}) — {item["total"]}'
                for i, item in enumerate(products, start=1)
            ),
            'Рецепты:',
            *(
                f'{r.name} — {r.author.username}'
                for r in Recipe.objects.filter(in_carts__user=request.user)
            ),
        ]))

        return FileResponse(
            report,
            filename="shopping_list.txt",
            as_attachment=True,
        )


class UserViewSet(DjoserUserViewSet):
    lookup_field = 'id'

    # /users/me/
    @action(detail=False, methods=('get',), permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    # аватар
    @action(detail=False, methods=('put', 'delete'),
            url_path='me/avatar', permission_classes=[IsAuthenticated])
    def avatar(self, request):
        if request.method == 'PUT':
            ser = AvatarSerializer(data=request.data, context={
                                   'request': request})
            ser.is_valid(raise_exception=True)
            request.user.avatar = ser.validated_data['avatar']
            request.user.save(update_fields=['avatar'])
            return Response({'avatar': request.user.avatar.url})
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # подписки
    @action(detail=False, methods=('get',),
            serializer_class=AuthorCardSerializer,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        authors = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = self.get_serializer(page, many=True,
                                         context={'request': request})
        return self.get_paginated_response(serializer.data)

    # подписаться / отписаться
    @action(detail=True, methods=('post', 'delete'),
            serializer_class=AuthorCardSerializer,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        author = self.get_object()

        if request.method == 'POST':
            if author == request.user:
                raise ValidationError({'errors': 'Нельзя подписаться на себя'})
            _, created = Follow.objects.get_or_create(
                user=request.user, author=author)
            if not created:
                raise ValidationError({'errors': 'Уже подписаны'})
            return Response(self.get_serializer(author).data,
                            status=status.HTTP_201_CREATED)

        # DELETE
        follow = Follow.objects.filter(
            user=request.user, author=author).first()
        if not follow:
            raise ValidationError({'errors': 'Подписки не существует'})  # 400
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
