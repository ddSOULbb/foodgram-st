from django.shortcuts import get_object_or_404, redirect
from recipes.models import Recipe


def recipe_short_redirect_view(request, link):
    """Редирект по короткой ссылке на рецепт."""
    recipe = get_object_or_404(Recipe, link=link)
    return redirect(f"/recipes/{recipe.id}/")
