import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase

from . import model_factories as mfactories
from ..models import (Contact, ADDRESS_TYPE_CHOICES, PHONE_TYPE_CHOICES,
                      EMAIL_TYPE_CHOICES)


class ContactTest(TestCase):
    def setUp(self):
        self.user_uuid = uuid.uuid4()

    def test_contact_save_minimal(self):
        contact = Contact(
            user_uuid=self.user_uuid,
            first_name='John',
            last_name='Misty',
            workflowlevel1_uuids=[str(uuid.uuid4)],
        )
        contact.full_clean()
        contact.save()

        contact_saved = Contact.objects.get(pk=contact.pk)
        self.assertEqual(contact_saved.first_name, contact.first_name)
        self.assertEqual(contact_saved.last_name, contact.last_name)

    def test_contact_save_fails_missing_user_uuid(self):
        contact = Contact(
            first_name='John',
            last_name='Misty',
        )
        self.assertRaises(ValidationError, contact.full_clean)

    def test_contact_save_fails_missing_name(self):
        contact = Contact(
            user_uuid=self.user_uuid,
            last_name='Misty',
        )
        self.assertRaises(ValidationError, contact.full_clean)

        contact = Contact(
            user_uuid=self.user_uuid,
            first_name='John',
        )
        self.assertRaises(ValidationError, contact.full_clean)

    def test_contact_save_no_address(self):
        contact = mfactories.Contact()

        contact_saved = Contact.objects.get(pk=contact.pk)
        self.assertEqual(contact_saved.title, contact.title)
        self.assertEqual(contact_saved.contact_type, contact.contact_type)
        self.assertEqual(contact_saved.customer_type, contact.customer_type)
        self.assertEqual(contact_saved.company, contact.company)
        self.assertEqual(contact_saved.addresses, [])
        self.assertEqual(contact_saved.emails, contact.emails)
        self.assertEqual(contact_saved.phones, contact.phones)
        self.assertEqual(contact_saved.notes, contact.notes)

    def test_contact_save_email_fail(self):
        contact = mfactories.Contact.build(emails=[
            {
                'type': None,
            }
        ])
        try:
            contact.full_clean()
        except ValidationError as error:
            self.assertIn('emails', error.error_dict)
            self.assertIn(
                ("Invalid value: {'type': None}. List of 'email' objects "
                 "with the structure:"),
                error.messages[0])
        else:
            self.fail('ValidationError was not raised')

        contact = mfactories.Contact.build()
        contact.emails = [{'type': 'private', 'email': 'contact'}]
        self.assertRaises(ValidationError, contact.full_clean)

    def test_contact_save_email_without_top_level_domain(self):
        contact = mfactories.Contact.build()
        contact.emails = [
            {'type': 'private', 'email': 'contact@localhost'}
        ]
        contact.full_clean()

    def test_contact_save_emails(self):
        mfactories.Contact.build(emails=[]).full_clean()

        for email_type in EMAIL_TYPE_CHOICES:
            mfactories.Contact.build(emails=[
                {
                    'type': str(email_type),
                    'email': 'email@example.com'
                }
            ]).full_clean()

    def test_contact_save_address_fail(self):
        contact = mfactories.Contact.build()
        contact.addresses = [
            {
                'type': None,
            }
        ]
        try:
            contact.full_clean()
        except ValidationError as error:
            self.assertIn('addresses', error.error_dict)
            self.assertIn(
                ("Invalid value: {'type': None}. List of 'address' objects "
                 "with the structure:"),
                error.messages[0])
        else:
            self.fail('ValidationError was not raised')

        contact.addresses = [
            {
                'type': 'invented',
            }
        ]
        self.assertRaises(ValidationError, contact.full_clean)

    def test_contact_save_address(self):
        for address_type in ADDRESS_TYPE_CHOICES:
            contact = mfactories.Contact.build(addresses=[
                {
                    'type': str(address_type),
                }
            ])
            contact.full_clean()

        contact = mfactories.Contact.build(addresses=[
            {
                'type': 'home',
                'street': 'Oderberger Straße',
                'house_number': '16A',
                'postal_code': '10435',
                'city': 'Berlin',
                'country': 'Germany',
            },
            {
                'type': 'billing',
                'street': 'Millán de Priego',
                'house_number': '44',
                'postal_code': '23004',
                'city': 'Jaén',
                'country': 'España',
            }
        ])
        contact.full_clean()

    def test_contact_save_phones_fail(self):
        contact = mfactories.Contact.build()
        contact.phones = [
            {
                'type': None,
            }
        ]
        try:
            contact.full_clean()
        except ValidationError as error:
            self.assertIn('phones', error.error_dict)
            self.assertIn(
                ("Invalid value: {'type': None}. List of 'phone' objects with "
                 "the structure:"),
                error.messages[0])
        else:
            self.fail('ValidationError was not raised')

        contact.phones = [
            {
                'type': 'invented',
            }
        ]
        self.assertRaises(ValidationError, contact.full_clean)

        contact.phones = [
            {
                'type': 'invented',
                'number': '99',
            }
        ]
        self.assertRaises(ValidationError, contact.full_clean)

        contact.phones = [
            {
                'type': 'invented',
                'number': '9'*21,
            }
        ]
        self.assertRaises(ValidationError, contact.full_clean)

    def test_contact_save_phones(self):
        mfactories.Contact.build(phones=[]).full_clean()

        for phone_type in PHONE_TYPE_CHOICES:
            mfactories.Contact.build(phones=[
                {
                    'type': str(phone_type),
                    'number': '911'
                }
            ]).full_clean()

    def test_contact_save_phones_unicode(self):
        mfactories.Contact.build(phones=[
            {
                u'type': u'mobile',
                u'number': u'911'
            }
        ]).full_clean()

    def test_string_representation(self):
        contact = Contact(
            user_uuid=self.user_uuid,
            first_name='Jóhn',
            last_name='Mïsty',
        )
        self.assertEqual(str(contact), 'Jóhn Mïsty')
