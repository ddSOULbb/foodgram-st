from io import StringIO

from api.pagination import RecipePagination
from api.permissions import IsAuthorOrReadOnly
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .serializers import (AddRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, ShortRecipeSerializer)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""

    serializer_class = RecipeSerializer
    pagination_class = RecipePagination
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        recipes = Recipe.objects.all()
        return recipes.select_related("author").prefetch_related("ingredients")

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return AddRecipeSerializer

    @action(
        detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            deleted_count, _ = Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).delete()

            if not deleted_count:
                return Response(
                    {"errors": "Рецепта нет в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True, methods=["GET"], url_path="get-link", permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        result = get_object_or_404(Recipe, pk=pk)
        return Response(
            {"short-link": request.build_absolute_uri(f"/s/{result.link}/")},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"errors": "Рецепт уже в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        items = ShoppingCart.objects.filter(user=request.user, recipe=recipe)

        if not items.exists():
            return Response(
                {"errors": "Рецепта нет в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _format_shopping_list(self, ingredients):
        output = StringIO()
        output.write("Список покупок:\n")
        for name, data in ingredients.items():
            line = f"- {name} ({data['measurement_unit']}) - {data['amount']}\n"
            output.write(line)
        return output.getvalue()

    @action(
        detail=False,
        methods=["GET"],
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def download_basket(self, request):
        basket = request.user.shoppingcarts.all()
        ingredients = {}

        for result in basket:
            recipe_ingredients = result.recipe.recipeingredients.all()
            for ingredient in recipe_ingredients:
                name = ingredient.ingredient.name
                measurement_unit = ingredient.ingredient.measurement_unit
                amount = ingredient.amount

                if name in ingredients:
                    ingredients[name]["amount"] += amount
                else:
                    ingredients[name] = {
                        "measurement_unit": measurement_unit,
                        "amount": amount,
                    }

        return HttpResponse(
            self._format_shopping_list(ingredients),
            content_type="text/plain",
            headers={"Content-Disposition": 'attachment; filename="list.txt"'},
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def redirect_by_short_link(request, link):
    recipe = get_object_or_404(Recipe, link=link)
    return redirect(f"/recipes/{recipe.id}/")
