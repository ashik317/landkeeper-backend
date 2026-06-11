from django.urls import path

from apps.authentication.views import (
    UserListCreateAPIView,
    UserRetrieveUpdateDestroyAPIView
)

urlpatterns = [
    path("users/", UserListCreateAPIView.as_view(), name="user-list-create"),
    path("users/<uuid:alias>/", UserRetrieveUpdateDestroyAPIView.as_view(), name="user-detail"),
]