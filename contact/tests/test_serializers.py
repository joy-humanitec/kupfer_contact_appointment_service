import uuid
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from . import model_factories as mfactories
from ..serializers import ContactSerializer, ContactNameSerializer


class ContactSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_contains_expected_fields(self):
        contact = mfactories.Contact()

        request = self.factory.get('/')

        serializer_context = {
            'request': Request(request),
        }

        serializer = ContactSerializer(instance=contact,
                                       context=serializer_context)

        data = serializer.data

        keys = [
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
            'url',
            'phones',
            'company',
            'contact_type',
            'organization_uuid',
            'customer_type',
            'notes',
            'workflowlevel1_uuids',
            'emails',
            'customer_id',
        ]
        self.assertEqual(set(data.keys()), set(keys))

    def test_title_display_field(self):
        contact = mfactories.Contact(title='mr')
        request = self.factory.get('/')
        serializer_context = {'request': Request(request)}
        serializer = ContactSerializer(instance=contact,
                                       context=serializer_context)
        self.assertEqual(serializer['title_display'].value, "Mr.")

    def test_unique_customer_id_validate(self):
        organization_uuid = uuid.uuid4()
        mfactories.Contact(organization_uuid=organization_uuid, customer_id="abc")
        data = {'organization_uuid': organization_uuid,
                'customer_id': "abcd",
                'workflowlevel1_uuids': [str(uuid.uuid4()), ]}
        request = self.factory.get('/')
        request.user = mfactories.User()
        request.session = {
            'jwt_organization_uuid': organization_uuid,
        }
        serializer_context = {'request': Request(request)}
        serializer = ContactSerializer(data=data, context=serializer_context)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        data['customer_id'] = "abc"
        serializer = ContactSerializer(data=data, context=serializer_context)
        self.assertFalse(serializer.is_valid())
        with self.assertRaisesMessage(ValidationError, expected_message='customer_id is not unique in organization'):
            serializer.is_valid(raise_exception=True)


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
