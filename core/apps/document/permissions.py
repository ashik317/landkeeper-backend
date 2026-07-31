from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.organisation.models import OrganisationUser, OrganisationRoleChoices
from apps.tenant.models import Tenant

MANAGER_ROLES = {
    OrganisationRoleChoices.LANDLORD,
    OrganisationRoleChoices.ADMIN,
    OrganisationRoleChoices.LETTING_AGENT,
}


class DocumentPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if isinstance(user, Tenant):
            return request.method in SAFE_METHODS

        if request.method in SAFE_METHODS:
            return True

        return OrganisationUser.objects.filter(
            user=user, role__in=MANAGER_ROLES
        ).exists()

    def has_object_permission(self, request, view, obj):
        user = request.user

        if isinstance(user, Tenant):
            return request.method in SAFE_METHODS and obj.organisation_id == user.organisation_id

        if request.method in SAFE_METHODS:
            return OrganisationUser.objects.filter(
                user=user, organisation=obj.organisation
            ).exists()

        return OrganisationUser.objects.filter(
            user=user, organisation=obj.organisation, role__in=MANAGER_ROLES
        ).exists()