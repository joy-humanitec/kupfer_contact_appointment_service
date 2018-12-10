from unittest.mock import Mock, patch
import uuid

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

import contact.tests.model_factories as cfactories
from . import model_factories as mfactories
from ..serializers import ContactNameField, AppointmentDenormalizedSerializer


class ContactNameFieldTest(TestCase):
    def test_no_contact_uuid(self):
        obj = Mock(contact_uuid=None)
        field = ContactNameField()
        self.assertIsNone(field.get_attribute(obj))

    def test_contact_found(self):
        contact = cfactories.Contact()
        obj = Mock(contact_uuid=contact.uuid)
        field = ContactNameField()
        self.assertEqual(
            field.get_attribute(obj),
            {
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'middle_name': contact.middle_name,
                'uuid': contact.uuid
            }
        )

    @patch('appointment.serializers.logger')
    def test_contact_not_found(self, mock_logger):
        obj = Mock(contact_uuid=str(uuid.uuid4()))
        field = ContactNameField()
        self.assertIsNone(field.get_attribute(obj))
        self.assertTrue(mock_logger.warning.called)


class AppointmentDenormalizedSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = cfactories.User()
        self.user_uuid = uuid.uuid4()

    def test_contains_expected_fields(self):
        request = self.factory.get('/')
        serializer_context = {
            'request': Request(request),
        }
        appointment = mfactories.Appointment(owner=self.user_uuid)
        serializer = AppointmentDenormalizedSerializer(
            instance=appointment, context=serializer_context)
        data = serializer.data
        keys = [
            'uuid',
            'name',
            'end_date',
            'url',
            'notes',
            'start_date',
            'organization_uuid',
            'contact',
            'contact_uuid',
            'address',
            'siteprofile_uuid',
            'invitee_uuids',
            'workflowlevel2_uuids',
            'type',
            'id',
        ]
        self.assertEqual(set(data.keys()), set(keys))
