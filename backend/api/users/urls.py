from django.urls import include, path
from djoser.views import UserViewSet
from rest_framework.routers import DefaultRouter

from .views import UsersViewSet

router = DefaultRouter()
router.register("users", UsersViewSet, basename="users")

urlpatterns = [
    path("users/set_password/", UserViewSet.as_view({"post": "set_password"})),
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
