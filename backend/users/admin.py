from django.contrib import admin
from .models import User, Subscription


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name',
                    'last_name', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    search_help_text = 'Поиск по нику или email'
    list_filter = ('is_staff', 'is_active')
    ordering = ('id',)

    @admin.display(description="Блокировка")
    def is_active_display(self, obj):
        return obj.is_active


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subscribed_to')
    search_fields = ('user__username', 'subscribed_to__username')
    list_filter = ('user',)
