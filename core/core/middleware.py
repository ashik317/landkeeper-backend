import uuid

from django.http import JsonResponse

from apps.organisation.enums import OrganisationRoleChoices
from apps.organisation.models import OrganisationUser


class OrganisationHeaderMiddleware:
    HEADER = "X-LANDLORD-ALIAS"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.header_organisation = None

        landlord_alias = request.headers.get(self.HEADER, "").strip()
        if landlord_alias:
            try:
                uuid.UUID(landlord_alias)
            except ValueError:
                return JsonResponse({"error": "Invalid landlord alias."}, status=400)

            landlord = (
                OrganisationUser.objects.select_related("organisation")
                .filter(
                    user__alias=landlord_alias,
                    role=OrganisationRoleChoices.LANDLORD,
                    organisation__is_active=True,
                )
                .first()
            )
            if not landlord:
                return JsonResponse({"error": "Landlord not found."}, status=404)

            request.header_organisation = landlord.organisation

        return self.get_response(request)