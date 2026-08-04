from rest_framework import permissions
from apps.authentication.models import User
from apps.organisation.models import OrganisationUser


class IsLandlord(permissions.BasePermission):
    message = "Only landlords can perform this action."

    def has_permission(self, request, view):
        if not isinstance(request.user, User):
            return False

        organisation_user = OrganisationUser.objects.filter(user=request.user).first()
        return bool(organisation_user and organisation_user.role == "LANDLORD")