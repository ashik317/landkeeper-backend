from django.urls import path, include

urlpatterns = [
    path("auth", include("api.urls.auth")),
    path("organisation", include("api.urls.organisation")),
    path("users", include("api.urls.users")),
    path("property", include("api.urls.property")),
]
