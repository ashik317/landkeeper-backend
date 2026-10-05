from rest_framework.exceptions import ValidationError, NotFound


def get_request_organisation(request):
    user = request.user

    if user.is_superuser:
        organisation = getattr(request, "organisation", None)
        if not organisation:
            raise ValidationError(
                {
                    "landlord_alias": "X-LANDLORD-ALIAS header is required for super admin."
                }
            )
        return organisation

    organisation = user.get_organisation()
    if not organisation:
        raise NotFound("Organisation not found for the user.")
    return organisation
