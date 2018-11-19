# -*- coding: utf-8 -*-
import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase

from . import model_factories as mfactories
from ..models import Contact, ADDRESS_TYPE_CHOICES, PHONE_TYPE_CHOICES


class ContactTest(TestCase):
    def setUp(self):
        self.user_uuid = uuid.uuid4()

    def test_contact_save_minimal(self):
        contact = Contact.objects.create(
            user_uuid=self.user_uuid,
            first_name='John',
            last_name='Misty',
            workflowlevel1_uuids=[str(uuid.uuid4)],
        )

        contact_saved = Contact.objects.get(pk=contact.pk)
        self.assertEqual(contact_saved.first_name, 'John')
        self.assertEqual(contact_saved.last_name, 'Misty')

    def test_contact_save_fails_missing_user_uuid(self):
        contact = Contact(
            first_name='John',
            last_name='Misty',
        )
        self.assertRaises(ValidationError, contact.save)

    def test_contact_save_fails_missing_name(self):
        contact = Contact(
            user_uuid=self.user_uuid,
            last_name='Misty',
        )
        self.assertRaises(ValidationError, contact.save)

        contact = Contact(
            user_uuid=self.user_uuid,
            first_name='John',
        )
        self.assertRaises(ValidationError, contact.save)

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

    def test_contact_save_fails_wrong_email(self):
        contact = mfactories.Contact()
        contact.emails = [{'type': 'private', 'email': 'contact'}]
        self.assertRaises(ValidationError, contact.save)

    def test_contact_save_address_fail(self):
        contact = mfactories.Contact()
        contact.addresses = [
            {
                'type': None,
            }
        ]
        self.assertRaises(ValidationError, contact.save)

        contact.addresses = [
            {
                'type': 'invented',
            }
        ]
        self.assertRaises(ValidationError, contact.save)

    def test_contact_save_address(self):
        for address_type in ADDRESS_TYPE_CHOICES:
            mfactories.Contact(addresses=[
                {
                    'type': str(address_type),
                }
            ])

        mfactories.Contact(addresses=[
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

    def test_contact_save_phones_fail(self):
        contact = mfactories.Contact()
        contact.phones = [
            {
                'type': None,
            }
        ]
        self.assertRaises(ValidationError, contact.save)

        contact.phones = [
            {
                'type': 'invented',
            }
        ]
        self.assertRaises(ValidationError, contact.save)

        contact.phones = [
            {
                'type': 'invented',
                'number': '99',
            }
        ]
        self.assertRaises(ValidationError, contact.save)

        contact.phones = [
            {
                'type': 'invented',
                'number': '9'*21,
            }
        ]
        self.assertRaises(ValidationError, contact.save)

    def test_contact_save_phones(self):
        mfactories.Contact(phones=[])

        for phone_type in PHONE_TYPE_CHOICES:
            mfactories.Contact(phones=[
                {
                    'type': str(phone_type),
                    'number': '911'
                }
            ])

    def test_contact_save_phones_unicode(self):
        mfactories.Contact(phones=[
            {
                u'type': u'mobile',
                u'number': u'911'
            }
        ])

    def test_unicode_representation(self):
        contact = Contact(
            user_uuid=self.user_uuid,
            first_name='John',
            last_name='Misty',
        )
        self.assertEqual(str(contact), 'John Misty')
