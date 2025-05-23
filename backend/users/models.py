from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from foodgram.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_USERNAME


class User(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        verbose_name="Никнейм",
        validators=[UnicodeUsernameValidator(), ],
    )

    first_name = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        verbose_name="Имя"
    )

    last_name = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        verbose_name="Фамилия"
    )

    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
        verbose_name="Электронная почта"
    )

    avatar = models.ImageField(
        upload_to="users/avatars",
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки."""

    author = models.ForeignKey(
        User, verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="authors"
    )

    subscriber = models.ForeignKey(
        User,
        verbose_name="Подписан",
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ("author__username",)
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "author"],
                name="unique_subscription"
            ),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F("author")),
                name="self_subscription"
            ),
        ]

    def __str__(self):
        return f"{self.subscriber} подписан на {self.author}"
