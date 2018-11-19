from uuid import UUID

from django import forms
import django_filters
from rest_framework import exceptions

from .models import Appointment

CURRENT_USER_FILTER_KEYWORD = 'me'


class DateRangeWidget(django_filters.widgets.SuffixedMultiWidget):
    suffixes = ['gte', 'lte']

    def __init__(self, attrs=None):
        widgets = (forms.TextInput, forms.TextInput)
        super(DateRangeWidget, self).__init__(widgets, attrs)


class AppointmentFilter(django_filters.FilterSet):
    owner = django_filters.CharFilter(
        method="owner_filter",
        help_text='Can either be a UUID or "me", to display only the events '
                  'owned by the current logged in user')
    invitee = django_filters.CharFilter(
        method="invitee_filter",
        help_text='Can either be a UUID or "me", to display only the events '
                  'to which the current logged in user is invited')
    workflowlevel2_uuid = django_filters.CharFilter(
        method='workflowlevel2_uuid_filter',
        help_text='UUID for the project'
    )
    start_date = django_filters.DateFromToRangeFilter(widget=DateRangeWidget())

    class Meta:
        model = Appointment
        fields = ['contact_uuid', 'owner', 'invitee', 'workflowlevel2_uuid',
                  'start_date']

    def owner_filter(self, queryset, field_name, value):
        if value == CURRENT_USER_FILTER_KEYWORD:
            my_uuid = self.request.session.get('jwt_user_uuid')

            return queryset.filter(owner=my_uuid)
        else:
            try:
                UUID(value)
            except ValueError:
                raise exceptions.ValidationError(
                    'owner field can only have value "{}" or a valid User UUID'
                    .format(CURRENT_USER_FILTER_KEYWORD))
            else:
                return queryset.filter(owner=value)

    def invitee_filter(self, queryset, field_name, value):
        if value == CURRENT_USER_FILTER_KEYWORD:
            return queryset.filter(invitee_uuids__contains=[
                self.request.session.get('jwt_user_uuid')])
        else:
            try:
                UUID(value)
            except ValueError:
                raise exceptions.ValidationError(
                    'invitee field can only have value "{}" or a valid '
                    'User UUID'.format(CURRENT_USER_FILTER_KEYWORD))
            else:
                return queryset.filter(invitee_uuids__contains=[value])

    def workflowlevel2_uuid_filter(self, queryset, field_name, value):
        try:
            UUID(value)
        except ValueError:
            raise exceptions.ValidationError(
                'workflowlevel2_uuids field can only have a valid UUID'
                .format(CURRENT_USER_FILTER_KEYWORD))
        else:
            return queryset.filter(workflowlevel2_uuids__contains=[value])
