from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_token(token):
    from apps.authentication.models import User
    from apps.tenant.models import Tenant

    try:
        validated_token = AccessToken(token)
        user_id = validated_token["user_id"]
        user_type = validated_token.get("user_type", "staff")
    except (InvalidToken, TokenError):
        return AnonymousUser()

    try:
        if user_type == "tenant":
            return Tenant.objects.get(id=user_id)
        return User.objects.get(id=user_id)
    except (User.DoesNotExist, Tenant.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        scope["user"] = await get_user_from_token(token) if token else AnonymousUser()

        return await self.app(scope, receive, send)