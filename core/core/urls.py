from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    path("auth/", include("api.urls.social")),
    path("auth/", include("api.urls.authentication")),
    path("auth/", include("api.urls.users")),
    path("accounts/", include("allauth.urls"))
]
