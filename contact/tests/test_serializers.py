from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from . import model_factories as mfactories
from ..serializers import ContactSerializer, ContactNameSerializer


class ContactSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.keys = [
            'uuid',
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'addresses',
            'siteprofile_uuids',
            'workflowlevel2_uuids',
            'title',
            'title_display',
            'suffix',
            'phones',
            'company',
            'contact_type',
            'organization_uuid',
            'customer_type',
            'notes',
            'workflowlevel1_uuids',
            'emails',
            'customer_id',
            'create_date',
            'edit_date',
        ]

    def test_contains_expected_fields(self):
        contact = mfactories.Contact()

        request = self.factory.get('/')

        serializer_context = {
            'request': Request(request),
        }

        serializer = ContactSerializer(instance=contact,
                                       context=serializer_context)

        data = serializer.data

        self.assertEqual(set(data.keys()), set(self.keys))

    def test_contains_expected_fields_w_contact_type_name(self):
        global_type = mfactories.Type(is_global=True)
        contact = mfactories.Contact(contact_type=global_type)
        request = self.factory.get('/')
        serializer_context = {'request': Request(request)}
        serializer = ContactSerializer(instance=contact, context=serializer_context)
        data = serializer.data
        extended_keys = self.keys + ['contact_type_name']
        self.assertEqual(set(data.keys()), set(extended_keys))

    def test_title_display_field(self):
        contact = mfactories.Contact(title='mr')
        request = self.factory.get('/')
        serializer_context = {'request': Request(request)}
        serializer = ContactSerializer(instance=contact,
                                       context=serializer_context)
        self.assertEqual(serializer['title_display'].value, "Mr.")


class ContactNameSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_contains_expected_fields(self):
        contact = mfactories.Contact()

        serializer = ContactNameSerializer(instance=contact)

        data = serializer.data

        keys = [
            'uuid',
            'first_name',
            'middle_name',
            'last_name',
            'title',
            'id',
        ]

        self.assertEqual(set(data.keys()), set(keys))
