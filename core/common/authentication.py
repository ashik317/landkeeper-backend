from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings

from apps.property.models import Tenant


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_type = validated_token.get("user_type")

        # -------------------------
        # TENANT LOGIN
        # -------------------------
        if user_type == "tenant":
            tenant_id = validated_token.get(api_settings.USER_ID_CLAIM)
            if tenant_id is None:
                raise InvalidToken(
                    _("Token contained no recognizable tenant identification")
                )

            try:
                tenant = Tenant.objects.get(**{api_settings.USER_ID_FIELD: tenant_id})
            except Tenant.DoesNotExist:
                raise AuthenticationFailed(
                    _("Tenant not found"), code="tenant_not_found"
                )

            if not tenant.is_active:
                raise AuthenticationFailed(
                    _("Tenant is inactive"), code="tenant_inactive"
                )

            return tenant

        # -------------------------
        # DEFAULT USER LOGIN
        # -------------------------
        return super().get_user(validated_token)
