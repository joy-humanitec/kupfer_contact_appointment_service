# -*- coding: utf-8 -*-
import logging
import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.core.validators import validate_email

from datetime import datetime

logger = logging.getLogger(__name__)


class Appointment(models.Model):
    uuid = models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)
    owner = models.UUIDField()
    name = models.CharField(max_length=50, help_text='Name')
    start_date = models.DateTimeField(help_text='Start date')
    end_date = models.DateTimeField(help_text='End date')
    type = ArrayField(models.CharField(max_length=50))
    address = models.CharField(max_length=100, help_text='Address')
    siteprofile_uuid = models.UUIDField(
        blank=True, null=True, help_text='Address where it takes place')
    invitee_uuids = ArrayField(
        models.UUIDField(), blank=True, null=True,
        help_text='List of TolaUser UUIDs invited to the appointment.')
    organization_uuid = models.UUIDField(blank=True, null=True)
    workflowlevel2_uuids = ArrayField(
        models.UUIDField(), blank=True, null=True,
        help_text='List of WorkflowLevel2s added to the appointment.')
    notes = models.CharField(
        max_length=500, help_text='Notes', blank=True, null=True)
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
        return u'{} {}'.format(self.name, self.start_date)


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
        return u'{} ({})'.format(self.appointment, self.sent_at)
