from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from foodgram.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_USERNAME
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from users.models import Subscription

from .validators import validate_username

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            "is_subscribed",
            "avatar",
            "first_name",
            "last_name",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriber.filter(subscribed_to=obj).exists()
        )


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="Этот email уже зарегистрирован"
            )
        ],
    )
    username = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="Это имя пользователя уже занято"
            ),
            validate_username,
        ],
    )
    first_name = serializers.CharField(required=True, max_length=MAX_LENGTH_USERNAME,)
    last_name = serializers.CharField(required=True, max_length=MAX_LENGTH_USERNAME,)

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name", "password")

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result.pop("password", None)
        return result

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ["avatar"]

    def validate(self, attrs):
        if "avatar" not in attrs:
            raise serializers.ValidationError(
                {"avatar": "Поле аватара является обязательным."}
            )
        return attrs


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        model = Subscription
        fields = ("user", "subscribed_to")
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=("user", "subscribed_to"),
                message="Вы уже подписаны на этого пользователя",
            )
        ]

    def validate(self, data):
        if data["user"] == data["subscribed_to"]:
            raise serializers.ValidationError("Нельзя подписаться на самого себя.")
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(instance.subscribed_to, context=self.context).data


class SubscriptionSerializer(UserSerializer):
    """Сериализатор информации о подписках."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        # циклический импорт, без него никак
        from api.recipes.serializers import ShortRecipeSerializer

        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")
        recipes = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[: int(recipes_limit)]
        return ShortRecipeSerializer(recipes, many=True, context=self.context).data
