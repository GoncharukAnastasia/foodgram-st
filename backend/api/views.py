from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter

from djoser.views import UserViewSet as DjoserUserViewSet

from recipes.models import Tag, Ingredient, Recipe, Favorite
from shopping_cart.models import ShoppingCart
from .permissions import IsAuthorOrReadOnly

# вот сюда обязательно добавьте AvatarSerializer и UserSerializer
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeShortSerializer,
    UserSerializer,
    AvatarSerializer,
    SubscriptionSerializer,
)

from users.models import Follow

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            qs = qs.filter(name__istartswith=name)
        return qs


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tags", "recipe_ingredients__ingredient"
    )
    permission_classes = (IsAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # фильтрация по автору
        author = self.request.query_params.get("author")
        if author:
            qs = qs.filter(author__id=author)

        # фильтры по избранному и корзине
        user = self.request.user
        if user.is_authenticated:
            if self.request.query_params.get("is_favorited") == "1":
                qs = qs.filter(favorites__user=user)
            if self.request.query_params.get("is_in_shopping_cart") == "1":
                qs = qs.filter(in_carts__user=user)

        return qs

    def create(self, request, *args, **kwargs):
        write_ser = RecipeWriteSerializer(data=request.data,
                                          context={'request': request})
        write_ser.is_valid(raise_exception=True)
        recipe = write_ser.save()
        read_ser = RecipeReadSerializer(recipe,
                                        context={'request': request})
        return Response(read_ser.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        write_ser = RecipeWriteSerializer(instance=recipe,
                                          data=request.data,
                                          context={'request': request},
                                          partial=True)
        write_ser.is_valid(raise_exception=True)
        recipe = write_ser.save()
        read_ser = RecipeReadSerializer(recipe,
                                        context={'request': request})
        return Response(read_ser.data)

    partial_update = update

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        url = request.build_absolute_uri(
            reverse("recipe-detail", args=[pk])
        )
        return Response({"short-link": url})

    def _make_short(self, recipe):
        ser = RecipeShortSerializer(recipe, context={'request': self.request})
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True,
            methods=("post", "delete"),
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            fav, created = Favorite.objects.get_or_create(user=user,
                                                          recipe=recipe)
            if not created:
                return Response(
                    {"errors": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return self._make_short(recipe)

        deleted, _ = Favorite.objects.filter(user=user,
                                             recipe=recipe).delete()
        if not deleted:
            return Response(
                {"errors": "Рецепт не был в избранном"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=("post", "delete"),
            url_path="shopping_cart",
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            item, created = ShoppingCart.objects.get_or_create(user=user,
                                                               recipe=recipe)
            if not created:
                return Response(
                    {"errors": "Рецепт уже в корзине"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return self._make_short(recipe)

        deleted, _ = ShoppingCart.objects.filter(user=user,
                                                 recipe=recipe).delete()
        if not deleted:
            return Response(
                {"errors": "Рецепт не был в корзине"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=("get",))
    def download_shopping_cart(self, request):
        ingrs = (
            Ingredient.objects
            .filter(recipes__in_carts__user=request.user)
            .values("name", "measurement_unit")
            .annotate(amount=Sum("ingredient_recipes__amount"))
            .order_by("name")
        )
        lines = [f"{i['name']} ({i['measurement_unit']}) — {i['amount']}"
                 for i in ingrs]
        content = "\n".join(lines)
        resp = HttpResponse(content, content_type="text/plain")
        resp["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'
        return resp


class UserViewSet(DjoserUserViewSet):
    lookup_field = "id"

    @action(detail=False,
            methods=["get"],
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        user = request.user
        if request.method == "PUT":
            ser = AvatarSerializer(data=request.data, context={
                                   "request": request})
            ser.is_valid(raise_exception=True)
            user.avatar = ser.validated_data["avatar"]
            user.save()
            # возвращаем _только_ url аватара
            return Response(
                {"avatar": user.avatar.url},
                status=status.HTTP_200_OK
            )
        # DELETE
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        serializer_class=SubscriptionSerializer,        # Важно!
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        me = request.user

        # Нельзя подписаться на себя
        if author == me:
            return Response(
                {"errors": "Нельзя подписаться на себя"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Обрабатываем recipes_limit из query params
        limit = request.query_params.get("recipes_limit")
        try:
            limit = int(limit) if limit is not None else None
        except ValueError:
            limit = None

        if request.method == "POST":
            _, created = Follow.objects.get_or_create(user=me, author=author)
            if not created:
                return Response(
                    {"errors": "Уже подписаны"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # готовим данные через SubscriptionSerializer
            qs = author.recipes.all()
            if limit is not None:
                qs = qs[:limit]
            # пробрасываем в контекст, чтобы is_subscribed правильно считался
            serializer = SubscriptionSerializer(
                author, context={"request": request}
            )
            data = serializer.data
            # подменяем список рецептов и recipes_count
            data["recipes"] = RecipeShortSerializer(
                qs, many=True, context={"request": request}
            ).data
            data["recipes_count"] = author.recipes.count()
            return Response(data, status=status.HTTP_201_CREATED)

        # DELETE
        deleted, _ = Follow.objects.filter(user=me, author=author).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        recipes_limit = request.query_params.get("recipes_limit")
        authors = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(authors)

        result = []
        for author in page:
            qs = author.recipes.all()
            if recipes_limit:
                qs = qs[:int(recipes_limit)]
            author_data = UserSerializer(author,
                                         context={"request": request}).data
            author_data["recipes"] = RecipeShortSerializer(
                qs, many=True, context={"request": request}
            ).data
            author_data["recipes_count"] = author.recipes.count()
            result.append(author_data)
        return self.get_paginated_response(result)

    def _subscription_payload(self, author, request, limit=None):
        qs = author.recipes.all()
        if limit is not None:
            qs = qs[:int(limit)]
        data = SubscriptionSerializer(
            author, context={"request": request}).data
        data["recipes"] = (RecipeShortSerializer
                           (qs, many=True,
                            context={"request": request}).data)
        data["recipes_count"] = author.recipes.count()
        return data
