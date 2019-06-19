import json
import uuid

from django.test import TestCase

from rest_framework.test import APIRequestFactory

from contact.models import Type
from . import model_factories as mfactories
from ..views import TypeViewSet


class ContactTypeBaseViewsTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.organization_uuid = str(uuid.uuid4())
        self.user = mfactories.User()
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_core_user_uuid': uuid.uuid4(),
            'jwt_username': 'Test User',
        }


class ContactTypeListViewsTest(ContactTypeBaseViewsTest):

    def test_list_global_and_org_contact_types(self):
        org_type = mfactories.Type(
            organization_uuid=self.organization_uuid,
            is_global=False
        )
        global_type = mfactories.Type(
            is_global=True
        )
        org_global_type = mfactories.Type(
            organization_uuid=self.organization_uuid,
            is_global=True
        )
        another_org_not_global_type = mfactories.Type()

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = TypeViewSet.as_view({'get': 'list'})
        response = view(request)
        response.render()
        response_uuids = [x['uuid'] for x in json.loads(response.content)]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)
        self.assertIn(str(org_type.uuid), response_uuids)
        self.assertIn(str(global_type.uuid), response_uuids)
        self.assertIn(str(org_global_type.uuid), response_uuids)
        self.assertNotIn(str(another_org_not_global_type.uuid), response_uuids)


class ContactTypeCreateViewsTest(ContactTypeBaseViewsTest):

    def test_create_content_type(self):
        data = {
            "name": "new test type"
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = TypeViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        org_type = Type.objects.get()
        self.assertEqual(org_type.name, data['name'])
        self.assertEqual(str(org_type.organization_uuid), self.organization_uuid)
        self.assertFalse(org_type.is_global)


class ContactTypeUpdateViewsTest(ContactTypeBaseViewsTest):

    def test_update_org_contact_type(self):
        org_type = mfactories.Type(
            organization_uuid=self.organization_uuid,
            is_global=False,
            name='a Test Type'
        )
        request = self.factory.patch('', {'name': 'still a test type'})
        request.user = self.user
        request.session = self.session
        view = TypeViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=org_type.pk)

        self.assertEqual(response.status_code, 200)
        org_type.refresh_from_db()
        self.assertEqual(org_type.name, "still a test type")


class ContactTypeDeleteViewsTest(ContactTypeBaseViewsTest):

    def test_delete_org_contact_type(self):
        org_type = mfactories.Type(
            organization_uuid=self.organization_uuid,
            is_global=False,
            name='a Test Type'
        )
        request = self.factory.delete('')
        request.user = self.user
        request.session = self.session
        view = TypeViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=org_type.pk)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Type.objects.count(), 0)

    def test_delete_fail_another_org_contact_type(self):
        org_type = mfactories.Type()
        request = self.factory.delete('')
        request.user = self.user
        request.session = self.session
        view = TypeViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=org_type.pk)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Type.objects.count(), 1)

    def test_delete_fail_another_org_global_contact_type(self):
        org_type = mfactories.Type(
            is_global=True
        )
        request = self.factory.delete('')
        request.user = self.user
        request.session = self.session
        view = TypeViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=org_type.pk)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Type.objects.count(), 1)
