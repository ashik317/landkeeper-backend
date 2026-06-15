from django.urls import path
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView


class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:8000/auth/social/google/"
    client_class = OAuth2Client


urlpatterns = [
    path("social/google/", GoogleLoginView.as_view(), name="google-login"),
]