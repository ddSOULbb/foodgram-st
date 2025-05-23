from api.recipes.short_serializers import ShortRecipeSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import Subscription, User


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, label="Аватар")

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and request.user.subscriptions.filter(author=obj).exists()
        )


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
    class Meta:
        model = Subscription
        fields = ("subscriber", "author")
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=("subscriber", "author"),
                message="Вы уже подписаны на этого пользователя.",
            )
        ]

    def validate(self, data):
        if data["subscriber"] == data["author"]:
            error = "Нельзя подписаться на самого себя."
            raise serializers.ValidationError(error)
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.author,
            context=self.context
        ).data


class SubscriptionSerializer(UserSerializer):
    """Сериализатор информации о подписках."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="recipes.count")

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")
        recipes = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[: int(recipes_limit)]
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context
        ).data
