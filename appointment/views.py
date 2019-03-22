import django_filters
from rest_framework import viewsets, filters, mixins
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

from .filters import AppointmentFilter
from .models import Appointment, AppointmentNotification, AppointmentNote
from .permissions import (OrganizationPermission,
                          AppointmentNotificationPermission, AppointmentNoteOrganizationPermission)
from .serializers import (AppointmentSerializer,
                          AppointmentNotificationSerializer, AppointmentNoteSerializer)

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class DefaultCursorPagination(CursorPagination):
    """
    TODO move this to settings to provide better standardization
    See http://www.django-rest-framework.org/api-guide/pagination/
    """
    page_size = 30
    max_page_size = 2000
    page_size_query_param = 'page_size'


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Appointments. A common use for them is to set events in a calendar.

    list:
    Lists all the appointments which belong to the same user's organization.
    """
    start_date_lte = openapi.Parameter('start_date_lte', openapi.IN_QUERY,
                                       type=openapi.TYPE_STRING)
    start_date_gte = openapi.Parameter('start_date_gte', openapi.IN_QUERY,
                                       type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[start_date_lte, start_date_gte])
    def list(self, request):
        # Use this or the ordering filter won't work
        queryset = self.filter_queryset(self.get_queryset())
        organization_uuid = request.session.get('jwt_organization_uuid')
        queryset = queryset.filter(organization_uuid=organization_uuid)
        queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def perform_create(self, serializer):
        core_user_uuid = self.request.session.get('jwt_core_user_uuid')
        organization_uuid = self.request.session.get('jwt_organization_uuid')
        serializer.save(owner=core_user_uuid,
                        organization_uuid=organization_uuid)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super(AppointmentViewSet, self).update(request, *args, **kwargs)

    ordering_fields = ('id', 'start_date', 'end_date')
    lookup_field = 'uuid'
    ordering = ('id',)
    filter_class = AppointmentFilter
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.OrderingFilter
    )
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    pagination_class = DefaultCursorPagination
    permission_classes = (OrganizationPermission,)


class AppointmentNotificationViewSet(viewsets.ModelViewSet):
    """
    Appointment Notifications.
    """
    def list(self, request):
        # Use this or the ordering filter won't work
        queryset = self.filter_queryset(self.get_queryset())
        organization_uuid = self.request.session.get('jwt_organization_uuid')
        queryset = queryset.filter(
            appointment__organization_uuid=organization_uuid)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super(AppointmentNotificationViewSet,
                     self).update(request, *args, **kwargs)

    ordering_fields = ('id',)
    filter_backends = (filters.OrderingFilter,)
    queryset = AppointmentNotification.objects.all()
    serializer_class = AppointmentNotificationSerializer
    permission_classes = (AppointmentNotificationPermission,)


class AppointmentNoteViewSet(mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             viewsets.GenericViewSet):

    queryset = AppointmentNote.objects.all()
    permission_classes = (AppointmentNoteOrganizationPermission, )
    serializer_class = AppointmentNoteSerializer
