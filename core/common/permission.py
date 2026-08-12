from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.authentication.models import User
from apps.organisation.enums import OrganisationRoleChoices
from apps.organisation.models import OrganisationUser
from apps.property.models import (
    Tenant,
    MortgageAdviserPropertyPermission,
    MortgageAdviserMortgagePermission,
)


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

class IsAdmin(BasePermission):
    message = "Only administrators can perform this action."
    def has_permission(self, request, view):
        if not isinstance(request.user, User):
            return False
        return OrganisationUser.objects.filter(
            user=request.user,
            role=OrganisationRoleChoices.ADMIN,
        ).exists()

class IsMortgageAdviser(BasePermission):
    message = "Only mortgage advisers can perform this action."

    def has_permission(self, request, view):
        if not isinstance(request.user, User):
            return False
        return OrganisationUser.objects.filter(
            user=request.user,
            role=OrganisationRoleChoices.MORTGAGE_ADVISER,
        ).exists()


class CanAccessMortgageAdviserProperty(BasePermission):
    message = "You do not have permission to access this property."

    def has_object_permission(self, request, view, obj):
        permission = MortgageAdviserPropertyPermission.objects.filter(
            mortgage_adviser=request.user,
            property=obj,
        ).first()

        if not permission:
            return False

        if request.method in SAFE_METHODS:
            return permission.can_view

        return permission.can_edit


class CanAccessMortgageAdviserMortgage(BasePermission):
    message = "You do not have permission to access this mortgage."

    def has_object_permission(self, request, view, obj):
        permission = MortgageAdviserMortgagePermission.objects.filter(
            mortgage_adviser=request.user,
            mortgage=obj,
        ).first()

        if not permission:
            return False

        if request.method in SAFE_METHODS:
            return permission.can_view

        return permission.can_edit
