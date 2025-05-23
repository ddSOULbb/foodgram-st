from api.users.serializers import (SubscriptionCreateSerializer,
                                   SubscriptionSerializer,
                                   UserAvatarSerializer)
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import User


class UsersViewSet(DjoserUserViewSet):
    """ViewSet для работы с пользователями"""

    lookup_url_kwarg = "pk"

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = self.request.user
        serializer = self.get_serializer(user, context={"request": request})
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        subscriber = request.user
        author = get_object_or_404(User, pk=pk)

        serializer = SubscriptionCreateSerializer(
            data={"subscriber": subscriber.id, "author": author.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)

        deleted, _ = user.subscriptions.filter(author=author).delete()
        if not deleted:
            raise ValidationError("Вы не подписаны на этого пользователя.")

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(authors__subscriber=user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["PUT"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def upload_avatar(self, request):
        user = request.user
        serializer = UserAvatarSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"avatar": user.avatar.url})

    @upload_avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar.delete()
        return Response(
            {"detail": "Аватар успешно удален"},
            status=status.HTTP_204_NO_CONTENT
        )
