from rest_framework import serializers
from recipes.models import Ingredient, Recipe, RecipeIngredient
from django.contrib.auth import get_user_model
from api.users.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField


User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class ShortRecipeSerializer(serializers.ModelSerializer):
    """
    Урезанный сериализатор для рецепта для ответов
    при добавлении в избранное/список покупок.
    """

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов и количества."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'ingredients', 'cooking_time',
            'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return request.user.shoppingcarts.filter(recipe=obj).exists()

    def get_ingredients(self, obj):
        result = obj.recipeingredients.all()
        return RecipeIngredientSerializer(result, many=True).data

    def get_short_link(self, obj):
        request = self.context.get('request')
        return obj.get_short_url(request)


class AddRecipeIngredientSerializer(serializers.Serializer):
    """Сериализатор для добавления ингредиента к рецепту."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    def to_internal_value(self, data):
        if isinstance(data.get("amount"), str):
            data["amount"] = int(data["amount"])
        return super().to_internal_value(data)


class AddRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта."""

    ingredients = AddRecipeIngredientSerializer(many=True, min_length=1)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = [
            'ingredients', 'image', 'name', 'text',
            'cooking_time', 'link'
        ]

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Не может быть пустым.")
        return value

    def validate_ingredients(self, value):
        ingredient_ids = {ingredient['id'] for ingredient in value}
        if len(value) > len(ingredient_ids):
            raise serializers.ValidationError(
                "Не может быть одинаковых ингредиентов")
        return value

    def validate_cooking_time(self, value):
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    def load_new_recipe(self, recipe, ingredients_data):
        if not recipe.link:
            recipe.generate_link()
            recipe.save()
        if ingredients_data:
            recipe.recipeingredients.all().delete()
            recipe.recipeingredients.bulk_create([
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients_data
            ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        recipe = super().create(validated_data)
        self.load_new_recipe(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' not in self.initial_data:
            raise serializers.ValidationError({
                'ingredients': 'Поле ingredients обязательно'
            })
        ingredients_data = validated_data.pop('ingredients', None)
        recipe = super().update(instance, validated_data)
        self.load_new_recipe(recipe, ingredients_data)
        return recipe


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сокращенный сериализатор для рецептов."""

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class AddFavoriteAndShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецептов в избранное и список покупок."""

    class Meta:
        model = None
        fields = ['user', 'recipe']

    def __init__(self, *args, **kwargs):
        self.Meta.model = kwargs.pop('model')
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        serializer = RecipeShortSerializer(instance.recipe)
        return serializer.data
