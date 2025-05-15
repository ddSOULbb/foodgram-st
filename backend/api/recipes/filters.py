import django_filters
from recipes.models import Recipe, Ingredient
from django_filters import rest_framework as filters


class RecipeFilter(filters.FilterSet):
    """Фидьтр рецептов"""

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['author']

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated:
            if value:
                return queryset.filter(favorites__user=self.request.user)
            return queryset.exclude(favorites__user=self.request.user)
        return queryset.none() if value else queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            if value:
                return queryset.filter(shoppingcarts__user=self.request.user)
            return queryset.exclude(shoppingcarts__user=self.request.user)
        return queryset.none() if value else queryset


class IngredientFilter(django_filters.FilterSet):
    """Фильтр ингридиентов."""

    name = django_filters.CharFilter(lookup_expr='contains')

    class Meta:
        model = Ingredient
        fields = ['name']
