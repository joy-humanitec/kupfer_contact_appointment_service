from rest_framework import viewsets, filters
from rest_framework.response import Response

from .models import Contact
from .permissions import ContactPermission  # ContactPermission
from .serializers import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """
    User's contacts.
    """
    def list(self, request):
        # Use this or the ordering filter won't work
        queryset = self.filter_queryset(self.get_queryset())
        organization_uuid = request.session.get('jwt_organization_uuid')
        queryset = queryset.filter(organization_uuid=organization_uuid)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        user_uuid = self.request.session.get('jwt_user_uuid')
        organization_uuid = self.request.session.get('jwt_organization_uuid')
        serializer.save(user_uuid=user_uuid,
                        organization_uuid=organization_uuid)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super(ContactViewSet, self).update(request, *args, **kwargs)

    ordering_fields = ('first_name',)
    filter_backends = (filters.OrderingFilter,)
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = (ContactPermission,)
