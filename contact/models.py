import uuid

from django.contrib.postgres.fields import ArrayField, HStoreField
from django.contrib.postgres.indexes import GinIndex
from django.db import models

from .validators import validate_emails, validate_phones, validate_addresses


TITLE_CHOICES = (
    ('mr', 'Mr.'),
    ('ms', 'Ms.'),
    ('mrs', 'Mrs.'),
    ('miss', 'Miss'),
    ('family', 'Family'),
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
    core_user_uuid = models.UUIDField(blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, help_text='First name', db_index=True)
    middle_name = models.CharField(max_length=50, blank=True, help_text='Middle name (not common in Germany)')
    last_name = models.CharField(max_length=50, blank=True, help_text='Surname or family name')
    title = models.CharField(
        max_length=16, choices=TITLE_CHOICES, blank=True, null=True,
        help_text='Choices: {}'.format(
            ", ".join([kv[0] for kv in TITLE_CHOICES])))
    suffix = models.CharField(max_length=50, blank=True, help_text='Suffix for titles like dr., prof., dr. med. etc.')
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
                                                 ADDRESS_TYPE_CHOICES])),
                           validators=[validate_addresses])
    siteprofile_uuids = ArrayField(models.UUIDField(), blank=True, null=True,
                                   help_text='List of SiteProfile UUIDs')
    emails = ArrayField(HStoreField(), blank=True, null=True,
                        help_text="""
                               List of 'email' objects with the structure:
                               type (string - Choices: {}),
                               email (string)
                               """.format(", ".join([k for k in
                                                     EMAIL_TYPE_CHOICES])),
                        validators=[validate_emails])
    phones = ArrayField(HStoreField(), blank=True, null=True,
                        help_text="""
                               List of 'phone' objects with the structure:
                               type (string - Choices: {}),
                               number (string)
                               """.format(", ".join([k for k in
                                                     PHONE_TYPE_CHOICES])),
                        validators=[validate_phones])
    notes = models.TextField(blank=True, null=True)
    organization_uuid = models.CharField(max_length=36, blank=True, null=True,
                                         verbose_name='Organization UUID', db_index=True)
    workflowlevel1_uuids = ArrayField(models.CharField(max_length=36),
                                      help_text='List of Workflowlevel1 UUIDs')
    workflowlevel2_uuids = ArrayField(models.CharField(max_length=36),
                                      blank=True, null=True,
                                      help_text='List of Workflowlevel2 UUIDs')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        indexes = [
            GinIndex(fields=['workflowlevel1_uuids']),
            GinIndex(fields=['workflowlevel2_uuids'])
        ]
