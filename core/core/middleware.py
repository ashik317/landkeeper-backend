from django.http import JsonResponse

from apps.organisation.models import Organisation


class OrganisationHeaderMiddleware:
    HEADER = "X-ORGANISATION-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.header_organisation = None

        org_id = request.headers.get(self.HEADER, "").strip()
        if org_id:
            if not org_id.isdigit():
                return JsonResponse({"error": "Invalid organisation id."}, status=400)

            organisation = Organisation.objects.filter(id=org_id, is_active=True).first()
            if not organisation:
                return JsonResponse({"error": "Organisation not found."}, status=404)

            request.header_organisation = organisation

        return self.get_response(request)