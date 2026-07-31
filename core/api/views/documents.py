from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from apps.document.models import Document
from apps.document.permissions import DocumentPermission
from api.serializers.documents import DocumentSerializer


class DocumentsListCreateAPIView(ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [DocumentPermission]

    def get_queryset(self):
        return Document.objects.all()


class DocumentsRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [DocumentPermission]
    lookup_field = "alias"

    def get_queryset(self):
        return Document.objects.all()