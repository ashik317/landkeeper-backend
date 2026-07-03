from rest_framework import permissions
from apps.organisation.models import OrganisationUser


class IsLandlord(permissions.BasePermission):
    message = "Only landlords can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        organisation_user = OrganisationUser.objects.filter(
            user=request.user
        ).first()
        return bool(organisation_user and organisation_user.role == "LANDLORD")