from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticatedOrReadOnly


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or request.user == obj.author
