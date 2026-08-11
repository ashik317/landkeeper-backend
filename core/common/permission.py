from rest_framework.permissions import BasePermission

from apps.organisation.enums import OrganisationRoleChoices
from apps.organisation.models import OrganisationUser
from apps.property.models import Tenant

class IsTenant(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, Tenant) and request.user.is_authenticated

class IsTenantOrLandlord(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if isinstance(user, Tenant):
            return request.method in ["GET", "POST"]
        is_landlord = OrganisationUser.objects.filter(
            user=user,
            role=OrganisationRoleChoices.LANDLORD,
        ).exists()
        if is_landlord:
            return request.method == "GET"
        return False

class IsTenantOrLandlordForMaintenance(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if isinstance(user, Tenant):
            return request.method in ["GET", "PUT", "PATCH", "DELETE"]

        is_landlord = OrganisationUser.objects.filter(
            user=user,
            role=OrganisationRoleChoices.LANDLORD,
        ).exists()

        if is_landlord:
            return request.method in ["GET", "PUT", "PATCH"]

        return False