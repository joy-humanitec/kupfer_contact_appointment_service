# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import uuid

from django.contrib.postgres.fields import ArrayField, HStoreField
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from voluptuous import Schema, Any, All, Length

TITLE_CHOICES = (
    ('mr', 'Mr.'),
    ('ms', 'Ms.'),
)

CONTACT_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('supplier', 'Supplier'),
    ('producer', 'Producer'),
    ('personnel', 'Personnel'),
)

CUSTOMER_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('company', 'Company'),
    ('public', 'Public'),
)

ADDRESS_TYPE_CHOICES = (
    'home',
    'billing',
    'business',
    'delivery',
    'mailing',
)

PHONE_TYPE_CHOICES = (
    'office',
    'mobile',
    'home',
    'fax',
)

EMAIL_TYPE_CHOICES = (
    'office',
    'private',
    'other',
)


class Contact(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    user_uuid = models.UUIDField(blank=True, null=True)
    first_name = models.CharField(max_length=50, help_text='First name')
    middle_name = models.CharField(
        max_length=50, blank=True, null=True,
        help_text='Middle name (not common in Germany)')
    last_name = models.CharField(max_length=50,
                                 help_text='Surname or family name')
    title = models.CharField(
        max_length=2, choices=TITLE_CHOICES, blank=True, null=True,
        help_text='Choices: {}'.format(
            ", ".join([kv[0] for kv in TITLE_CHOICES])))
    contact_type = models.CharField(
        max_length=30, choices=CONTACT_TYPE_CHOICES, blank=True, null=True,
        help_text='Choices: {}'.format(
            ", ".join([kv[0] for kv in CONTACT_TYPE_CHOICES])))
    customer_type = models.CharField(
        max_length=30, choices=CUSTOMER_TYPE_CHOICES, blank=True, null=True,
        help_text='Choices: {}'.format(
            ", ".join([kv[0] for kv in CUSTOMER_TYPE_CHOICES])))
    company = models.CharField(max_length=100, blank=True, null=True)
    addresses = ArrayField(HStoreField(), blank=True, null=True,
                           help_text="""
                           List of 'address' objects with the structure:
                           type (string - Choices: {}),
                           street (string),
                           house_number (string),
                           postal_code: (string),
                           city (string),
                           country (string)
                           """.format(", ".join([k for k in
                                                 ADDRESS_TYPE_CHOICES])))
    siteprofile_uuids = ArrayField(models.UUIDField(), blank=True, null=True,
                                   help_text='List of SiteProfile UUIDs')
    emails = ArrayField(HStoreField(), blank=True, null=True,
                        help_text="""
                               List of 'email' objects with the structure:
                               type (string - Choices: {}),
                               email (string)
                               """.format(", ".join([k for k in
                                                     EMAIL_TYPE_CHOICES])))
    phones = ArrayField(HStoreField(), blank=True, null=True,
                        help_text="""
                               List of 'phone' objects with the structure:
                               type (string - Choices: {}),
                               number (string)
                               """.format(", ".join([k for k in
                                                     PHONE_TYPE_CHOICES])))
    notes = models.TextField(blank=True, null=True)
    organization_uuid = models.CharField(max_length=36, blank=True, null=True,
                                         verbose_name='Organization UUID')
    workflowlevel1_uuids = ArrayField(models.CharField(max_length=36),
                                      help_text='List of Workflowlevel1 UUIDs')
    workflowlevel2_uuids = ArrayField(models.CharField(max_length=36),
                                      blank=True, null=True,
                                      help_text='List of Workflowlevel2 UUIDs')

    def _validate_address(self, address):
        schema = Schema({
            'type': All(Any(str), Any(*ADDRESS_TYPE_CHOICES)),
            'street': All(Any(str), Length(max=100)),
            'house_number': All(Any(str), Length(max=20)),
            'postal_code': All(Any(str), Length(max=20)),
            'city': All(Any(str), Length(max=85)),
            'country': All(Any(str), Length(max=50)),
        })
        schema(address)

    def _validate_email(self, email):
        schema = Schema({
            'type': All(Any(str), Any(*EMAIL_TYPE_CHOICES)),
            'email': All(Any(str), Length(min=3, max=254)),
        })
        validate_email(email['email'])
        schema(email)

    def _validate_phone(self, phone):
        schema = Schema({
            'type': All(Any(str), Any(*PHONE_TYPE_CHOICES)),
            'number': All(Any(str), Length(min=3, max=20)),
        })
        schema(phone)

    def clean_fields(self, exclude=None):
        super(Contact, self).clean_fields(exclude=exclude)
        if self.addresses:
            for address in self.addresses:
                try:
                    self._validate_address(address)
                except Exception as error:
                    raise ValidationError(error)

        if self.emails:
            for email in self.emails:
                try:
                    self._validate_email(email)
                except Exception as error:
                    raise ValidationError(error)

        if self.phones:
            for phone in self.phones:
                try:
                    self._validate_phone(phone)
                except Exception as error:
                    raise ValidationError(error)

    def __str__(self):
        return u'{} {}'.format(self.first_name, self.last_name)
