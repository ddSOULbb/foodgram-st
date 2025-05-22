import random
import string

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from foodgram.constants import (LENGTH_SHORT_LINK, MAX_INGREDIENT_AMOUNT,
                                MAX_LENGTH_LINK, MAX_LENGTH_RECIPE,
                                MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT)

User = get_user_model()


class PublishedModel(models.Model):
    """Базовая модель."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        "Recipe", on_delete=models.CASCADE, verbose_name="Рецепт"
    )

    class Meta:
        abstract = True
        ordering = ("user",)


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField(
        max_length=MAX_LENGTH_RECIPE, unique=True, verbose_name="Название"
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_RECIPE, verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_name_measurement_unit"
            )
        ]
        ordering = ("name",)

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", verbose_name="Ингредиенты"
    )
    name = models.CharField(max_length=MAX_LENGTH_RECIPE, verbose_name="Название")
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления",
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f"Время приготовления должно быть не менее {MIN_COOKING_TIME} минуты.",
            )
        ],
    )
    link = models.CharField(
        max_length=MAX_LENGTH_LINK,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Ссылка",
    )
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    image = models.ImageField(upload_to="images/", verbose_name="Картинка")
    text = models.TextField(verbose_name="Описание")

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        default_related_name = "recipes"
        ordering = ("-pub_date",)

    def __str__(self):
        return self.name

    def generate_link(self):
        length = LENGTH_SHORT_LINK
        chars = string.ascii_letters

        while True:
            self.link = "".join(random.choices(chars, k=length))
            if not Recipe.objects.filter(link=self.link).exists():
                break
        return self.link


class RecipeIngredient(models.Model):
    """Ингредиент в рецепте."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт",)
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message=f"Количество должно быть не менее {MIN_INGREDIENT_AMOUNT}",
            ),
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT,
                message=f"Количество должно быть больше {MAX_INGREDIENT_AMOUNT}",
            ),
        ],
    )

    class Meta:
        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиентов"
        default_related_name = "recipeingredients"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_recipe_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.ingredient.name}"


class Favorite(PublishedModel):
    """Избранные рецепты."""

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        default_related_name = "favorites"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_recipe"
            )
        ]

    def __str__(self):
        return f"{self.user}"


class ShoppingCart(PublishedModel):
    """Список покупок."""

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        default_related_name = "shoppingcarts"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_ShoppingCart"
            )
        ]

    def __str__(self):
        return f"{self.user}"
