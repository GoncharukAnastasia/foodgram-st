# recipes/admin.py
from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart
)


#  фильтр коротко / средне / долго
class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время готовки"
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        # уникальные значения, отсортированные по возрастанию
        times = sorted({*model_admin.get_queryset(request)
                        .values_list("cooking_time", flat=True)})
        if len(times) < 3:          
            return []

        third = len(times) // 3 or 1
        n = times[third - 1]
        m = times[2 * third - 1]

        short_cnt = sum(t < n for t in times)
        med_cnt = sum(n <= t < m for t in times)
        long_cnt = len(times) - short_cnt - med_cnt

        return [
            ("short", f"быстрее {n} мин ({short_cnt})"),
            ("medium", f"до {m} мин ({med_cnt})"),
            ("long", f"дольше {m} мин ({long_cnt})"),
        ]

    def queryset(self, request, qs):
        val = self.value()
        if not val:
            return qs

        times = sorted({*qs.values_list("cooking_time", flat=True)})
        third = len(times) // 3 or 1
        n = times[third - 1]
        m = times[2 * third - 1]

        if val == "short":
            return qs.filter(cooking_time__lt=n)
        if val == "medium":
            return qs.filter(cooking_time__gte=n, cooking_time__lt=m)
        if val == "long":
            return qs.filter(cooking_time__gte=m)
        return qs


#  корзина
@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")


#  ингредиенты
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit", "recipes_count")
    search_fields = ("name", "measurement_unit")
    list_filter = ("measurement_unit",)
    ordering = ("name",)

    @admin.display(description="Рецептов")
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


# inline-форма для ингредиентов в рецепте
class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


#  рецепты
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "cooking_time", "author",
        "favorites_count", "products_list", "image_tag",
    )
    search_fields = ("name", "author__username")
    list_filter = (CookingTimeFilter, "author")
    inlines = (IngredientInline,)

    @admin.display(description="В избранном")
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description="Продукты")
    @mark_safe
    def products_list(self, recipe):
        return "<br>".join(
            f"{ri.ingredient.name} ({ri.amount} {ri.ingredient.measurement_unit})"
            for ri in recipe.recipe_ingredients.select_related("ingredient")
        )

    @admin.display(description="Изображение")
    @mark_safe
    def image_tag(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" width="50" height="50" '
                'style="border-radius:4px;" />'
            )
        return ""


#  избранное
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
