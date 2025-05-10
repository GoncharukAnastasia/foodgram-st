from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = settings.AUTH_USER_MODEL


class Tag(models.Model):
    """Тег рецепта: завтрак, обед, ужин."""
    name = models.CharField('Название', max_length=200, unique=True)
    color = models.CharField(
        'HEX‑цвет', max_length=7,
        unique=True,
        validators=[RegexValidator(
            regex=r'^#([A-Fa-f0-9]{6})$',
            message='Введите цвет в формате #RRGGBB'
        )]
    )
    slug = models.SlugField('Слаг', max_length=200, unique=True)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Базовый перечень продуктов (загружается из data)."""
    name = models.CharField('Название', max_length=200)
    measurement_unit = models.CharField('Ед. измерения', max_length=200)

    class Meta:
        ordering = ('id',)
        unique_together = ('name', 'measurement_unit')
        indexes = [models.Index(fields=['name'])]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Основная сущность — рецепт блюда."""
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipes', verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=200)
    image = models.ImageField(
        'Фото блюда', upload_to='recipes/images/'
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=[MinValueValidator(1)]
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag, related_name='recipes', verbose_name='Теги'
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        return self.name

    @property
    def in_favorites(self) -> int:
        """Сколько раз рецепт добавили в избранное."""
        return self.favorites.count()


class RecipeIngredient(models.Model):
    """Промежуточная таблица «ингредиент – количество – рецепт»."""
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredient_recipes'
    )
    amount = models.PositiveIntegerField(
        'Количество', validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = ('recipe', 'ingredient')
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self) -> str:
        return f'{self.ingredient} – {self.amount}'


class Favorite(models.Model):
    """Избранные рецепты пользователя."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites'
    )
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self) -> str:
        return f'{self.user} {self.recipe}'
