from __future__ import annotations

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
)
from users.models import Follow

User = get_user_model()

class AvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)


class UserSerializer(DjoserUserSerializer):
    """Базовый пользователь + avatar / is_subscribed."""

    avatar = serializers.ImageField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = (*DjoserUserSerializer.Meta.fields, "avatar", "is_subscribed")

    def get_is_subscribed(self, author):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and Follow.objects.filter(user=user, author=author).exists()
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = fields


class RecipeIngredientReadSerializer(serializers.ModelSerializer):  # ③
    id = serializers.PrimaryKeyRelatedField(
        source="ingredient", read_only=True)
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")
        read_only_fields = fields


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, source="recipe_ingredients", read_only=True
    )
    image = serializers.ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = fields

    # helpers
    def get_is_favorited(self, recipe):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=recipe).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=recipe).exists()
        )


class IngredientAmount(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmount(many=True, write_only=True)
    image = Base64ImageField(write_only=True, required=True)

    class Meta:
        model = Recipe
        fields = ("ingredients", "image", "name", "text", "cooking_time")

    # 0 / отрицательное
    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError('Минимум 1 минута')
        return value

    # пустой список или дубли ингредиентов
    def validate_ingredients(self, items):
        if not items:
            raise serializers.ValidationError('Нужен хотя бы один ингредиент')
        ids = [i['id'] for i in items]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Ингредиенты повторяются')
        return items

    # PATCH без `ingredients`  / пустая `image`
    def validate(self, attrs):
        if self.instance and 'ingredients' not in self.initial_data:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно.'}
            )
        if 'image' in self.initial_data and not self.initial_data['image']:
            raise serializers.ValidationError(
                {'image': 'Изображение не может быть пустым.'}
            )
        return attrs

    # helpers
    @staticmethod
    def _save_ingredients(recipe: Recipe, items):
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item["id"],
                amount=item["amount"],
            )
            for item in items
        )

    # create / update
    def create(self, validated_data):
        items = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, items)
        return recipe

    def update(self, instance, validated_data):
        items = validated_data.pop("ingredients", None)
        instance = super().update(instance, validated_data)         # ⑥
        if items is not None:
            self._save_ingredients(instance, items)
        return instance                                             # ⑥

    # отдаём «карточку» после POST / PATCH
    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class AuthorCardSerializer(UserSerializer):                        # ⑨
    """Автор + его рецепты (recipes_limit)."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source="recipes.count", read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, "recipes", "recipes_count")

    def get_recipes(self, author):
        limit = self.context["request"].query_params.get("recipes_limit")
        qs = author.recipes.all()
        if limit and limit.isdigit():
            qs = qs[: int(limit)]
        return RecipeShortSerializer(qs, many=True, context=self.context).data
