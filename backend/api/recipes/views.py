from io import StringIO
from django.db.models import Sum, F
from django.http import FileResponse
from recipes.models import RecipeIngredient
from api.pagination import RecipePagination
from api.permissions import IsAuthorOrReadOnly
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .serializers import (
    AddRecipeSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    FavoriteSerializer,
)

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

    def _handle_action(self, request, model, serializer_class, error_message):
        recipe = self.get_object()

        if request.method == "POST":
            serializer = serializer_class(
                data={"user": request.user.id, "recipe": recipe.id},
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(user=request.user,
                                          recipe=recipe).delete()
        if not deleted:
            return Response(
                {"errors": error_message}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._handle_action(
            request,
            model=Favorite,
            serializer_class=FavoriteSerializer,
            error_message="Рецепта нет в избранном.",
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.favorite(request, pk)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_action(
            request,
            model=ShoppingCart,
            serializer_class=ShoppingCartSerializer,
            error_message="Рецепта нет в списке покупок.",
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.shopping_cart(request, pk)

    def _format_shopping_list(self, ingredients):
        output = StringIO()
        output.write("Список покупок:\n")
        for name, data in ingredients.items():
            out = f"- {name} ({data['measurement_unit']}) - {data['amount']}\n"
            output.write(out)
        return output.getvalue()

    @action(
        detail=False,
        methods=["GET"],
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def download_basket(self, request):
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcarts__user=request.user)
            .values(name=F("ingredient__name"),
                    unit=F("ingredient__measurement_unit")
                    )
            .annotate(total=Sum("amount"))
            .order_by("name")
        )

        content = ""
        for item in ingredients:
            content += f"{item['name']} ({item['unit']}) — {item['total']}\n"

        response = FileResponse(
            content.encode("utf-8"),
            content_type="text/plain",
            filename="shopping_list.txt",
            as_attachment=True,
        )
        return response

    @action(
        detail=True,
        methods=["GET"],
        url_path="get-link",
        permission_classes=[AllowAny],
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        relative_url = reverse("recipe_short_redirect_view",
                               args=[recipe.link])
        full_url = request.build_absolute_uri(relative_url)
        return Response({"short-link": full_url}, status=status.HTTP_200_OK)
