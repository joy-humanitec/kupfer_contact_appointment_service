from django.db.models import Q
from django.http import HttpRequest
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response


class OrganizationExtensionMixin(object):
    """
    Extends the data with the organization from the JWT header for creation and validation in the serializer.
    """
    @staticmethod
    def _extend_request(request):
        data = request.data.copy()
        data['organization_uuid'] = request.session['jwt_organization_uuid']
        request_extended = Request(HttpRequest())
        request_extended._full_data = data
        return request_extended

    def create(self, request, *args, **kwargs):
        request_extended = self._extend_request(request)
        serializer = self.get_serializer(data=request_extended.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(organization_uuid=request_extended.data['organization_uuid'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        request_extended = self._extend_request(request)
        return super().update(request_extended, *args, **kwargs)


class OrganizationQuerySetWithGlobalFilterMixin(object):
    """
    Adds functionality to return a queryset filtered by the organization_uuid in the JWT header.
    If no jwt header is given, an empty queryset will be returned.
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        organization_uuid = self.request.session.get('jwt_organization_uuid', None)
        if not organization_uuid:
            return queryset.none()
        return queryset.filter(Q(organization_uuid=organization_uuid) | Q(is_global=True))

    def list(self, request, *args, **kwargs):
        """
        Filter for organization only if query-param is_global=False OR
        for global objects if is_global=True OR
        for organization AND global objects if is_global query-parm is passed.
        """
        if not request.query_params.get('is_global', 'false').lower() == 'true':
            queryset = super().get_queryset().filter(
                Q(organization_uuid=self.request.session['jwt_organization_uuid']) |
                Q(is_global=True))
        else:
            queryset = super().get_queryset().objects.all().filter(is_global=True)
        queryset = self.filter_queryset(queryset)
        if self.paginator:
            queryset = self.paginate_queryset(queryset)
            serializer = self.get_serializer(queryset, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
