from rest_framework.permissions import BasePermission
from apps.property.models import Tenant

class IsTenant(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, Tenant) and request.user.is_authenticated