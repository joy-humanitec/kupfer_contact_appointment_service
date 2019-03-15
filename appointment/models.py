import logging
import uuid

from datetime import datetime

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.core.validators import validate_email

from search_service_integration.mixins import SearchServiceIntegrationMixin
from search_service_integration.managers import SearchServiceIntegrationManager


logger = logging.getLogger(__name__)

NOTE_TYPE_PRIMARY, NOTE_TYPE_SECONDARY, NOTE_TYPE_TERTIARY,\
    NOTE_TYPE_QUATERNARY = 1, 2, 3, 4

NOTE_TYPES = (
    (NOTE_TYPE_PRIMARY, 'Primary'),
    (NOTE_TYPE_SECONDARY, 'Secondary'),
    (NOTE_TYPE_TERTIARY, 'OOO Reason'),
    (NOTE_TYPE_QUATERNARY, 'OOO Note'),
)


class AppointmentNote(models.Model):
    note = models.TextField()
    type = models.PositiveSmallIntegerField(choices=NOTE_TYPES, default=1, help_text='Choices: {}'.format(", ".join([str(kv[0]) for kv in NOTE_TYPES])))

    def __str__(self):
        return f'{self.type} - {self.note[:10]}'


class Appointment(SearchServiceIntegrationMixin, models.Model):
    uuid = models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)
    owner = models.UUIDField()
    name = models.CharField(max_length=50, help_text='Name', blank=True)
    start_date = models.DateTimeField(help_text='Start date')
    end_date = models.DateTimeField(help_text='End date')
    type = ArrayField(models.CharField(max_length=50))
    address = models.CharField(max_length=100, help_text='Address', blank=True)
    siteprofile_uuid = models.UUIDField(
        blank=True, null=True, help_text='Address where it takes place')
    invitee_uuids = ArrayField(
        models.UUIDField(), blank=True, null=True,
        help_text='List of CoreUser UUIDs invited to the appointment.')
    organization_uuid = models.UUIDField(blank=True, null=True)
    workflowlevel2_uuids = ArrayField(
        models.UUIDField(), blank=True, null=True,
        help_text='List of WorkflowLevel2s added to the appointment.')
    notes = models.ManyToManyField(AppointmentNote)
    contact_uuid = models.UUIDField(blank=True, null=True)

    def clean(self):
        super(Appointment, self).clean()

        if not isinstance(self.start_date, datetime):
            raise ValidationError("start_date is not of type datetime.")

        if not isinstance(self.end_date, datetime):
            raise ValidationError("end_date is not of type datetime.")

        if self.start_date > self.end_date:
            raise ValidationError("Start date cannot be later than end date.")

    def __str__(self):
        return f'{self.name} {self.start_date}'

    objects = SearchServiceIntegrationManager()

    def get_index_serializer(self):
        from .serializers import AppointmentSerializer
        return AppointmentSerializer(self)


class AppointmentNotification(models.Model):
    subject = models.CharField(max_length=100, help_text='Email Subject',
                               blank=True, null=True)
    message = models.TextField(help_text='Email Message', blank=True,
                               null=True)
    recipient = models.CharField(max_length=254, help_text='Email Recipient')
    sent_at = models.DateTimeField(help_text='Sent at', blank=True, null=True)
    send_notification = models.BooleanField(default=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    org_phone = models.CharField(max_length=20, blank=True, null=True,
                                 help_text='Organization Phone Number')
    org_name = models.CharField(max_length=50, blank=True, null=True,
                                help_text='Organization Name')

    def clean(self):
        super(AppointmentNotification, self).clean()
        validate_email(self.recipient)

    def __str__(self):
        return f'{self.appointment} ({self.sent_at})'
