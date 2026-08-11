from rest_framework.permissions import BasePermission
from apps.authentication.models import User
from apps.organisation.enums import OrganisationRoleChoices
from apps.organisation.models import OrganisationUser
from apps.property.models import Tenant

class IsTenant(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, Tenant) and request.user.is_authenticated


class IsLandlord(BasePermission):
    message = "Only landlords can perform this action."

    def has_permission(self, request, view):
        if not isinstance(request.user, User):
            return False
        return OrganisationUser.objects.filter(
            user=request.user,
            role=OrganisationRoleChoices.LANDLORD,
        ).exists()


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
