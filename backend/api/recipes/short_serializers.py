from recipes.models import Recipe
from rest_framework import serializers


# Либо циклический импорт в users, либо выносим в отдельный файл
class ShortRecipeSerializer(serializers.ModelSerializer):
    """Урезанный сериализатор рецепта для ответов"""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")
