from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscription, User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "recipes_count",
        "subscribers_count",
    )
    search_fields = ("username", "email")
    search_help_text = "Поиск по нику или email"
    list_filter = ("is_staff", "is_active")
    ordering = ("id",)

    @admin.display(description="Блокировка")
    def is_active_display(self, obj):
        return obj.is_active

    @admin.display(description="Рецептов")
    def recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description="Подписчиков")
    def subscribers_count(self, obj):
        return obj.followers.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "subscribed_to")
    search_fields = ("user__username", "subscribed_to__username")
    list_filter = ("user",)
