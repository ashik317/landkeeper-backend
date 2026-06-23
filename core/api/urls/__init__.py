from django.urls import path, include

urlpatterns = [
    path("/auth", include("api.urls.auth")),
    path("/organisation", include("api.urls.organisation")),
    path("", include("api.urls.property")),
]
