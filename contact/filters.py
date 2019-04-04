from django.db.models import Q
from django_filters import rest_framework as django_filters
from rest_framework import filters as drf_filters

from contact.models import Contact


class StartsWithSearchFilter(drf_filters.SearchFilter):

    search_param = 'starts_with'

    def get_search_fields(self, view, request):
        starts_with_search_fields = ('^first_name', '^last_name')
        return starts_with_search_fields


class BaseInArrayFilter(django_filters.BaseInFilter):

    def filter(self, qs, value):
        if not value:
            return qs
        params = Q()
        for item in value:
            params |= Q(**{f'{self.field_name}__contains': [item, ]})
        return qs.filter(params)


class ContactFilter(django_filters.FilterSet):
    workflowlevel2_uuids = BaseInArrayFilter()
    siteprofile_uuids = BaseInArrayFilter()

    class Meta:
        model = Contact
        fields = ('workflowlevel2_uuids', 'siteprofile_uuids', )
