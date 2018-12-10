from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from voluptuous import Schema, All, Any, Length
from voluptuous.error import MultipleInvalid

from . import models


def _get_clean_help_text(model, field_name):
    help_text = model._meta.get_field(field_name).help_text
    return ' '.join(help_text.split())


def validate_addresses(values):
    schema = Schema({
        'type': All(Any(str), Any(*models.ADDRESS_TYPE_CHOICES)),
        'street': All(Any(str), Length(max=100)),
        'house_number': All(Any(str), Length(max=20)),
        'postal_code': All(Any(str), Length(max=20)),
        'city': All(Any(str), Length(max=85)),
        'country': All(Any(str), Length(max=50)),
    })
    for value in values:
        try:
            schema(value)
        except MultipleInvalid:
            help_text = _get_clean_help_text(models.Contact, 'addresses')
            raise ValidationError(
                'Invalid value: %(value)s. %(help_text)s',
                params={'value': value, 'help_text': help_text},
                code='invalid')


def validate_emails(values):
    schema = Schema({
        'type': All(Any(str), Any(*models.EMAIL_TYPE_CHOICES)),
        'email': All(Any(str), Length(min=3, max=254)),
    })
    for value in values:
        try:
            schema(value)
        except MultipleInvalid:
            help_text = _get_clean_help_text(models.Contact, 'emails')
            raise ValidationError(
                'Invalid value: %(value)s. %(help_text)s',
                params={'value': value, 'help_text': help_text},
                code='invalid')
        else:
            validate_email(value['email'])


def validate_phones(values):
    schema = Schema({
        'type': All(Any(str), Any(*models.PHONE_TYPE_CHOICES)),
        'number': All(Any(str), Length(min=3, max=20)),
    })
    for value in values:
        try:
            schema(value)
        except MultipleInvalid:
            help_text = _get_clean_help_text(models.Contact, 'phones')
            raise ValidationError(
                'Invalid value: %(value)s. %(help_text)s',
                params={'value': value, 'help_text': help_text},
                code='invalid')
