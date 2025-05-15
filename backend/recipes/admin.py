from django.contrib import admin
from django.utils.html import format_html
from recipes.models import (
    Recipe, Ingredient, RecipeIngredient,
    Favorite, ShoppingCart
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн ингредиентов в рецепте."""

    model = RecipeIngredient
    extra = 0
    min_num = 1


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админка для количества ингредиентов."""

    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = ('name', 'author', 'favorites_count', 'preview_image')
    search_fields = ('name', 'author__username')
    search_help_text = "Поиск по рецепту и автору"
    list_filter = ('author',)
    readonly_fields = ('favorites_count',)
    inlines = (RecipeIngredientInline,)

    @admin.display(description='Картинка рецепта')
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<a href="{0}" target="_blank">'
                '<img src="{0}" style="height: 80px;"/></a>',
                obj.image.url
            )
        return '—'

    @admin.display(description='Добавления в избранное')
    def favorites_count(self, obj):
        return obj.favorites.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранных рецептов."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для списка покупок."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user',)
