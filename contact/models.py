import uuid

from django.contrib.postgres.fields import ArrayField, HStoreField
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Q
from django.db.models.constraints import UniqueConstraint
from django.db import models
from django.utils import timezone

from .validators import validate_emails, validate_phones, validate_addresses


TITLE_CHOICES = (
    ('mr', 'Mr.'),
    ('ms', 'Ms.'),
    ('mrs', 'Mrs.'),
    ('miss', 'Miss'),
    ('family', 'Family'),
)

CUSTOMER_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('contact', 'Contact'),
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


class Type(models.Model):
    """
    The Type model is used to set the `contact_type` field dynamically on the Contact model
    with custom choices per organization or global Types for all organizations.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, help_text="Name of the Type")
    organization_uuid = models.UUIDField('Organization UUID', db_index=True, help_text="UUID of the organization that has access to the Type, if it's not global.")
    is_global = models.BooleanField(default=False,  help_text="All organizations have access to global types.")

    def __str__(self):
        return self.name


class Contact(models.Model):
    """
    A Contact is a data model for an individual with common contact information.
    You can extend a BiFrost CoreUser by creating a one-to-one relationship between a Contact and a CoreUser
    using the `core_user_uuid` field.
    """
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    core_user_uuid = models.UUIDField(blank=True, null=True)
    customer_id = models.IntegerField(blank=True, null=True, help_text='ID set by the customer. Must be unique in organization.')
    first_name = models.CharField(max_length=50, blank=True, help_text='First name', db_index=True)
    middle_name = models.CharField(max_length=50, blank=True, help_text='Middle name (not common in Germany)')
    last_name = models.CharField(max_length=50, blank=True, help_text='Surname or family name')
    title = models.CharField(
        max_length=16, choices=TITLE_CHOICES, blank=True, null=True,
        help_text='Choices: {}'.format(
            ", ".join([kv[0] for kv in TITLE_CHOICES])))
    suffix = models.CharField(max_length=50, blank=True, help_text='Suffix for titles like dr., prof., dr. med. etc.')
    contact_type = models.ForeignKey(Type, blank=True, null=True, on_delete=models.SET_NULL)
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
    create_date = models.DateTimeField(default=timezone.now, editable=False)
    edit_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_default_customer_id(self) -> str:
        """Figure out next free unique customer_id and return it."""
        start_index = 10001
        try:
            latest_customer_id = self.__class__.objects.filter(
                organization_uuid=self.organization_uuid).exclude(
                customer_id=None).order_by('-customer_id').first().customer_id
            # latest_customer_id = ''.join(x for x in latest_customer_id if x.isdigit())
            next_customer_id = latest_customer_id + 1 if latest_customer_id else start_index
        except AttributeError:
            next_customer_id = start_index
        return next_customer_id

    def save(self, **kwargs):
        if not self.customer_id:
            self.customer_id = self.get_default_customer_id()
        super().save(**kwargs)

    class Meta:
        indexes = [
            GinIndex(fields=['workflowlevel1_uuids']),
            GinIndex(fields=['workflowlevel2_uuids']),
        ]
        constraints = [
            UniqueConstraint(
                name='unique_organization_customer_id',
                fields=['organization_uuid', 'customer_id'],
                condition=~Q(customer_id=None)
            )
        ]
