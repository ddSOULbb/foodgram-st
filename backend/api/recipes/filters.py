import django_filters
from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр рецептов"""

    is_favorited = filters.BooleanFilter(method="filter_boolean_field")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_boolean_field")

    class Meta:
        model = Recipe
        fields = ["author"]

    def filter_boolean_field(self, queryset, name, value):
        if not self.request.user.is_authenticated:
            return queryset.none() if value else queryset

        filter_map = {
            "is_favorited": "favorites__user",
            "is_in_shopping_cart": "shoppingcarts__user",
        }

        filter_field = filter_map.get(name)
        if not filter_field:
            return queryset

        if value:
            return queryset.filter(**{filter_field: self.request.user})
        return queryset.exclude(**{filter_field: self.request.user})


class IngredientFilter(django_filters.FilterSet):
    """Фильтр ингридиентов."""

    name = django_filters.CharFilter(lookup_expr="contains")

    class Meta:
        model = Ingredient
        fields = ["name"]
