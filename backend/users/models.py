from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from .constants import MAX_LENGTH_EMAIL, MAX_LENGTH_USERNAME, REGEX_NAME


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        unique=True, blank=True, max_length=MAX_LENGTH_EMAIL,
        verbose_name='Электронная почта'
    )
    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME, blank=True, unique=True,
        verbose_name='Имя пользователя',
        validators=[
            RegexValidator(
                regex=REGEX_NAME,
                message='Никнейм может содержать только буквы и цифры',
                code='invalid_username'
            )
        ]
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        blank=True,
        default=None
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'профиль пользователя'
        verbose_name_plural = 'профили пользователей'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscribed_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribed_to',
        verbose_name='Подписан на',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_to'],
                name='unique_subscriber_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('subscribed_to')),
                name='prevent_self_subscription',
            )
        ]

    def __str__(self):
        return f'Подписчик {self.user}'
