from api.pagination import RecipePagination
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription

from .serializers import (SubscriptionCreateSerializer, SubscriptionSerializer,
                          UserAvatarSerializer, UserRegistrationSerializer,
                          UserSerializer)

User = get_user_model()


class UsersViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с пользователями:
    - регистрация
    - получение информации о себе
    - загрузка и удаление аватара
    - подписка/отписка на других пользователей
    - список подписок
    """

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    pagination_class = RecipePagination

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegistrationSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=["GET"],
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def user_info(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["PUT"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def upload_avatar(self, request):
        user = request.user
        serializer = UserAvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"avatar": user.avatar.url})

    @upload_avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar.delete()
        return Response(
            {"detail": "Аватар успешно удален"}, status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=["POST"],
        url_path="subscribe",
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        """Подписывает текущего пользователя на другого пользователя."""
        subscribed_to = get_object_or_404(User, pk=pk)
        serializer = SubscriptionCreateSerializer(
            data={"user": request.user.id, "subscribed_to": subscribed_to.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        """Удаляет подписку текущего пользователя на другого."""
        subscribed_to = get_object_or_404(User, pk=pk)
        subscription = Subscription.objects.filter(
            user=request.user, subscribed_to=subscribed_to
        )
        if not subscription.exists():
            return Response(
                {"detail": "Подписка не найдена."}, status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["GET"],
        url_path="subscriptions",
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(
            subscribed_to__user=request.user
        ).prefetch_related("recipes")
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)
