from unittest.mock import Mock, patch
import uuid

from django.test import TestCase

import contact.tests.model_factories as cfactories
from ..serializers import ContactNameField


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
