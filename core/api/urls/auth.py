from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from api.views.auth import (
    GoogleLoginView,
    CustomLoginView
)

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("social/google/", GoogleLoginView.as_view(), name="google-login"),
]