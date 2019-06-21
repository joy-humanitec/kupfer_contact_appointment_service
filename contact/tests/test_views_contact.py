import json
import uuid

from django.db import transaction, IntegrityError
from django.test import TestCase

from rest_framework.test import APIRequestFactory

from . import model_factories as mfactories
from ..models import Contact, EMAIL_TYPE_CHOICES, PHONE_TYPE_CHOICES
from ..views import ContactViewSet


class ContactListViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = mfactories.User()
        self.organization_uuid = str(uuid.uuid4())
        self.wflvl1 = str(uuid.uuid4())
        self.wflvl2 = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_core_user_uuid': uuid.uuid4()
        }

    def test_list_empty(self):
        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])

    def test_list_contacts(self):
        siteprofile_uuids = [str(uuid.uuid4()), str(uuid.uuid4())]
        mfactories.Contact(
            first_name='David',
            addresses=[
                {
                    'type': 'billing',
                    'street': 'Bówie St',
                    'house_number': '22',
                    'postal_code': '78703',
                    'city': 'Austin',
                    'country': 'United States',
                },
            ],
            siteprofile_uuids=siteprofile_uuids,
            emails=[
                {'type': 'private', 'email': 'contact@bowie.co.uk'},
                {'type': 'office', 'email': 'bowie@label.co.uk'},
            ],
            notes="Bowie's notes",
            organization_uuid=self.organization_uuid,
            workflowlevel1_uuids=[self.wflvl1],
            workflowlevel2_uuids=[self.wflvl2],
        )

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        contact = response.data['results'][0]
        self.assertTrue('id' in contact)
        self.assertEqual(contact['first_name'], 'David')
        self.assertEqual(
            contact['addresses'],
            [
                {
                    'type': 'billing',
                    'street': 'Bówie St',
                    'house_number': '22',
                    'postal_code': '78703',
                    'city': 'Austin',
                    'country': 'United States',
                },
            ])
        self.assertEqual(contact['siteprofile_uuids'], siteprofile_uuids)
        self.assertEqual(
            contact['emails'],
            [
                {'type': 'private', 'email': 'contact@bowie.co.uk'},
                {'type': 'office', 'email': 'bowie@label.co.uk'},
            ])
        self.assertEqual(contact['notes'], "Bowie's notes")
        self.assertEqual(contact['organization_uuid'],
                         self.organization_uuid)
        self.assertEqual(contact['workflowlevel1_uuids'],
                         [self.wflvl1])
        self.assertEqual(contact['workflowlevel2_uuids'],
                         [self.wflvl2])

    def test_list_contacts_pagination_limit(self):
        mfactories.Contact.create_batch(
            size=51, **{'organization_uuid': self.organization_uuid,
                        'last_name': 'Rabbit'})

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 50)
        self.assertEqual(response.data['next'], 'http://testserver/?limit=50&offset=50')

    def test_list_contacts_diff_user_same_org(self):
        mfactories.Contact(
            first_name='David',
            addresses=[
                {
                    'type': 'billing',
                    'street': 'Bówie St',
                    'house_number': '22',
                    'postal_code': '78703',
                    'city': 'Austin',
                    'country': 'United States',
                },
            ],
            emails=[
                {'type': 'private', 'email': 'contact@bowie.co.uk'},
                {'type': 'office', 'email': 'bowie@label.co.uk'},
            ],
            notes="Bowie's notes",
            organization_uuid=self.organization_uuid,
        )
        request = self.factory.get('')
        user_other = mfactories.User(first_name='John', last_name='Lennon')
        request.user = user_other
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_contacts_diff_org(self):
        mfactories.Contact(
            first_name='David',
            addresses=[
                {
                    'type': 'billing',
                    'street': 'Bówie St',
                    'house_number': '22',
                    'postal_code': '78703',
                    'city': 'Austin',
                    'country': 'United States',
                },
            ],
            emails=[
                {'type': 'private', 'email': 'contact@bowie.co.uk'},
                {'type': 'office', 'email': 'bowie@label.co.uk'},
            ],
            notes="Bowie's notes",
            organization_uuid=self.organization_uuid,
        )
        request = self.factory.get('')
        user_other = mfactories.User(first_name='John', last_name='Lennon')
        request.user = user_other
        request.session = self.session
        request.session["jwt_organization_uuid"] = str(uuid.uuid4())
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

    def test_list_contacts_ordering_asc(self):
        mfactories.Contact.create_batch(
            size=2, **{'organization_uuid': self.organization_uuid})

        request = self.factory.get('', {'ordering': 'first_name'})
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['first_name'], 'David')
        self.assertEqual(response.data['results'][1]['first_name'], 'Nina')

    def test_list_contacts_ordering_desc(self):
        mfactories.Contact.create_batch(
            size=2, **{'organization_uuid': self.organization_uuid})

        request = self.factory.get('', {'ordering': '-first_name'})
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['first_name'], 'Nina')
        self.assertEqual(response.data['results'][1]['first_name'], 'David')

    def test_list_contacts_anonymoususer(self):
        request_get = self.factory.get('')
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request_get)
        self.assertEqual(response.status_code, 403)

    def test_search_startswith_case_insensitive(self):
        mfactories.Contact.create(
            first_name='David', last_name='Mueller',
            organization_uuid=self.organization_uuid)
        mfactories.Contact.create(
            first_name='Pyö', last_name='Mueller',
            organization_uuid=self.organization_uuid)
        # test first_name
        request = self.factory.get('?starts_with=dA')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        # test last_name
        request = self.factory.get('?starts_with=mueller')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # test not starts_with equals None
        request = self.factory.get('?starts_with=ueller')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

    def test_search_everywhere_case_insensitive(self):
        mfactories.Contact.create(
            first_name='David', last_name='Mueller',
            organization_uuid=self.organization_uuid)
        mfactories.Contact.create(
            first_name='Pyö', last_name='Mueller',
            organization_uuid=self.organization_uuid)
        # test first_name
        request = self.factory.get('?search=Avi')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        # test last_name
        request = self.factory.get('?search=ELLER')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # test not search equals None
        request = self.factory.get('?search=Rueller')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

    def test_several_workflowlevel2_uuids_filter(self):
        wfl2_1, wfl2_2, wfl2_3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        mfactories.Contact.create(
            workflowlevel2_uuids=[wfl2_1, ],
            organization_uuid=self.organization_uuid)
        mfactories.Contact.create(
            workflowlevel2_uuids=[wfl2_2, wfl2_1, ],
            organization_uuid=self.organization_uuid)
        mfactories.Contact.create(
            workflowlevel2_uuids=[wfl2_2, wfl2_3, ],
            organization_uuid=self.organization_uuid)
        mfactories.Contact.create(
            workflowlevel2_uuids=[uuid.uuid4(), ],
            organization_uuid=self.organization_uuid)
        request = self.factory.get(f'?workflowlevel2_uuids={wfl2_1},{wfl2_2}')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)

    def test_several_siteprofile_uuids_filter(self):
        wfl2_1, wfl2_2, wfl2_3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        mfactories.Contact.create(
            siteprofile_uuids=[wfl2_1, ],
            organization_uuid=self.organization_uuid)
        mfactories.Contact.create(
            siteprofile_uuids=[wfl2_2, wfl2_1, ],
            organization_uuid=self.organization_uuid)
        mfactories.Contact.create(
            siteprofile_uuids=[wfl2_2, wfl2_3, ],
            organization_uuid=self.organization_uuid)
        mfactories.Contact.create(
            siteprofile_uuids=[uuid.uuid4(), ],
            organization_uuid=self.organization_uuid)
        request = self.factory.get(f'?siteprofile_uuids={wfl2_1},{wfl2_2}')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)


class ContactRetrieveViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = mfactories.User()
        self.organization_uuid = str(uuid.uuid4())
        self.wflvl1 = str(uuid.uuid4())
        self.wflvl2 = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_core_user_uuid': uuid.uuid4()
        }

    def test_retrieve_contact(self):
        contact = mfactories.Contact(core_user_uuid=self.session[
            'jwt_core_user_uuid'],
                                     organization_uuid=self.organization_uuid)
        request = self.factory.get('')
        request.user = self.user
        request.session = self.session

        view = ContactViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=contact.pk)

        self.assertEqual(response.status_code, 200)

    def test_retrieve_contact_superuser(self):
        contact = mfactories.Contact(core_user_uuid=uuid.uuid4())
        request = self.factory.get('')
        su = mfactories.User()
        su.is_superuser = True
        su.save()

        request.user = su
        request.session = self.session

        view = ContactViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=contact.pk)

        self.assertEqual(response.status_code, 200)

    def test_retrieve_contact_diff_org(self):
        contact = mfactories.Contact(core_user_uuid=uuid.uuid4())
        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        request.session["jwt_organization_uuid"] = str(uuid.uuid4())
        view = ContactViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 403)

    def test_retrieve_contact_not_owner(self):
        contact = mfactories.Contact(core_user_uuid=uuid.uuid4())

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 403)

    def test_list_contacts_anonymoususer(self):
        request_get = self.factory.get('')
        view = ContactViewSet.as_view({'get': 'list'})
        response = view(request_get)
        self.assertEqual(response.status_code, 403)


class ContactCreateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = mfactories.User()
        self.organization_uuid = str(uuid.uuid4())
        self.wflvl1 = str(uuid.uuid4())
        self.wflvl2 = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_core_user_uuid': uuid.uuid4()
        }

    def test_create_contact_minimal(self):
        data = {
            'organization_uuid': 'ignore_this',
            'workflowlevel1_uuids': [self.wflvl1],
            'title_display': 'Dr.',
        }

        request = self.factory.post(  # trick to pass a list in a payload
            '', json.dumps(data), content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

        contact = Contact.objects.get(pk=response.data['id'])
        self.assertEqual(contact.core_user_uuid, self.session[
            'jwt_core_user_uuid'])
        self.assertEqual(contact.organization_uuid, self.organization_uuid)

    def test_create_contact_org_and_user_set_by_jwt(self):
        data = {
            'first_name': 'Máx',
            'last_name': 'Cöoper',
            'core_user_uuid': 'Test',
            'organization_uuid': 'ignore_this',
            'workflowlevel1_uuids': [self.wflvl1],
        }

        request = self.factory.post(  # trick to pass a list in a payload
            '', json.dumps(data), content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

        contact = Contact.objects.get(pk=response.data['id'])
        self.assertEqual(contact.core_user_uuid, self.session[
            'jwt_core_user_uuid'])
        self.assertEqual(contact.first_name, data['first_name'])
        self.assertEqual(contact.last_name, data['last_name'])
        self.assertEqual(contact.organization_uuid, self.organization_uuid)

    def test_create_contact_member_all_wflvl1s(self):
        wflvl1_other = str(uuid.uuid4())

        data = {
            'first_name': 'Máx',
            'last_name': 'Cöoper',
            'organization_uuid': 'ignore_this',
            'workflowlevel1_uuids': [self.wflvl1,
                                     wflvl1_other],
        }

        request = self.factory.post(  # trick to pass a list in a payload
            '', json.dumps(data), content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'create'})

        response = view(request)
        self.assertEqual(response.status_code, 201)

    def test_create_contact_member_all_wflvl1s_unordered_and_extra(self):
        wflvl1_other = str(uuid.uuid4())
        wflvl1_extra = str(uuid.uuid4())

        data = {
            'first_name': 'Máx',
            'last_name': 'Cöoper',
            'workflowlevel1_uuids': [wflvl1_other, wflvl1_extra,
                                     self.wflvl1],
        }

        request = self.factory.post(  # trick to pass a list in a payload
            '', json.dumps(data), content_type='application/json')
        request.user = self.user
        request.session = self.session

        view = ContactViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)

    def test_create_contact(self):
        siteprofile_uuid = uuid.uuid4()

        data = {
            'first_name': 'Julio',
            'middle_name': 'José',
            'last_name': 'Iglesias',
            'title': 'mr',
            'customer_type': 'customer',
            'company': 'Columbia',
            'addresses': [
                {
                    'type': 'home',
                    'street': 'Francisco de Sales',
                    'house_number': '288',
                    'postal_code': '28003',
                    'city': 'Madrid',
                    'country': 'Spain',
                },
            ],
            'siteprofile_uuids': [str(siteprofile_uuid)],
            'emails': [],
            'phones': [{'type': 'office', 'number': '123'}],
            'notes': 'I am the Spanish Gigolò',
            'workflowlevel1_uuids': [self.wflvl1],
            'workflowlevel2_uuids': [self.wflvl2],
        }

        request = self.factory.post(  # trick to pass structures in a payload
            '', json.dumps(data), content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'create'})

        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertDictContainsSubset(data, response.data)

        data['siteprofile_uuids'] = [siteprofile_uuid]
        contact = Contact.objects.get(pk=response.data['id'])
        self.assertDictContainsSubset(data, contact.__dict__)

    def test_create_with_invalid_email(self):
        data = {
            'first_name': u'Máx',
            'last_name': u'Cöoper',
            'organization_uuid': 'ignore_this',
            'workflowlevel1_uuids': [self.wflvl1],
            'emails': [{'type': EMAIL_TYPE_CHOICES[0], 'email': 'bad'}]
        }
        request = self.factory.post(  # trick to pass a list in a payload
            '', json.dumps(data), content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            str(response.data['emails'][0]), 'Enter a valid email address.')
        self.assertEqual(response.data['emails'][0].code, 'invalid')

    def test_create_with_invalid_phone(self):
        data = {
            'first_name': u'Máx',
            'last_name': u'Cöoper',
            'organization_uuid': 'ignore_this',
            'workflowlevel1_uuids': [self.wflvl1],
            'phones': [{'type': PHONE_TYPE_CHOICES[0], 'number': '01'}]
        }
        request = self.factory.post(  # trick to pass a list in a payload
            '', json.dumps(data), content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            ("Invalid value: {'type': 'office', 'number': '01'}. List of "
             "'phone' objects with the structure:"),
            str(response.data['phones'][0]),
        )
        self.assertEqual(response.data['phones'][0].code, 'invalid')

    def test_create_with_invalid_address(self):
        data = {
            'first_name': u'Máx',
            'last_name': u'Cöoper',
            'organization_uuid': 'ignore_this',
            'workflowlevel1_uuids': [self.wflvl1],
            'addresses': [
                {
                    'type': 'FAKE',
                    'street': 'Oderberger Straße',
                    'house_number': '16A',
                    'postal_code': '10435',
                    'city': 'Berlin',
                    'country': 'Germany',
                },
            ]
        }
        request = self.factory.post(  # trick to pass a list in a payload
            '', json.dumps(data), content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "List of 'address' objects with the structure:",
            str(response.data['addresses'][0]),
        )
        self.assertEqual(response.data['addresses'][0].code, 'invalid')

    def test_create_contacts_anonymoususer(self):
        request = self.factory.post('', {})
        view = ContactViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_create_contact_invalid_customer_id(self):
        mfactories.Contact(organization_uuid=self.organization_uuid,
                           customer_id='10001')
        data = {
            'workflowlevel1_uuids': [self.wflvl1],
            'customer_id': '10001',
        }

        request = self.factory.post('', data=json.dumps(data), content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'create'})
        try:
            with transaction.atomic():
                response = view(request)
        except IntegrityError:
            pass
        self.assertEqual(response.status_code, 400)
        contacts = Contact.objects.filter(organization_uuid=self.organization_uuid)
        self.assertEqual(contacts.count(), 1)


class ContactUpdateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = mfactories.User()
        self.organization_uuid = str(uuid.uuid4())
        self.wflvl1 = str(uuid.uuid4())
        self.wflvl2 = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_core_user_uuid': uuid.uuid4()
        }

    def test_update_contact_minimal(self):
        contact = mfactories.Contact(
            organization_uuid=self.organization_uuid,
            workflowlevel1_uuids=[self.wflvl1])
        data = {
            'first_name': 'David',
            'middle_name': 'Keith',
            'last_name': 'Lynch',
            'title_display': 'Dr.',
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'update'})

        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 200)

    def test_update_contact_w_contact_type(self):
        global_type = mfactories.Type(
            is_global=True
        )
        contact = mfactories.Contact(
            organization_uuid=self.organization_uuid,
            workflowlevel1_uuids=[self.wflvl1])
        data = {
            'contact_type': str(global_type.uuid),
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'update'})

        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 200)
        contact.refresh_from_db()
        self.assertEqual(contact.contact_type, global_type)

    def test_update_contact(self):
        siteprofile_uuid = uuid.uuid4()
        contact = mfactories.Contact(
            emails=[{
                'type': 'private',
                'email': 'emil@io.io',
            }],
            organization_uuid=self.organization_uuid,
            workflowlevel1_uuids=[self.wflvl1],
            customer_id='123',
        )

        data = {
            'first_name': 'David',
            'middle_name': 'Keith',
            'last_name': 'Lynch',
            'addresses': [
                {
                    'type': 'home',
                    'street': 'Francisco de Sales',
                    'house_number': '288',
                    'postal_code': '28003',
                    'city': 'Madrid',
                    'country': 'Spain',
                },
            ],
            'siteprofile_uuids': [str(siteprofile_uuid)],
            'emails': [],
            'phones': [
                {
                    'type': 'office',
                    'number': '12345',
                },
                {
                    'type': 'mobile',
                    'number': '67890',
                },
            ],
            'notes': 'My notes',
            'organization_uuid': 'ignore_this',
            'workflowlevel1_uuids': [self.wflvl1],
            'workflowlevel2_uuids': [self.wflvl2],
            'customer_id': '123',
        }
        request = self.factory.post('', json.dumps(data),
                                    content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'update'})

        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 200, response.data)

        contact = Contact.objects.get(pk=response.data['id'])
        data['siteprofile_uuids'] = [siteprofile_uuid]
        data['organization_uuid'] = self.organization_uuid
        self.assertDictContainsSubset(data, contact.__dict__)

    def test_update_contact_belonging_to_user_org(self):
        contact = mfactories.Contact(organization_uuid=self.organization_uuid)

        data = {
            'last_name': 'Lynch',
            'workflowlevel1_uuids': [self.wflvl1],
        }
        request = self.factory.post('', json.dumps(data),
                                    content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'update'})

        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 200, response.data)

        contact = Contact.objects.get(pk=response.data['id'])
        data['organization_uuid'] = self.organization_uuid
        self.assertDictContainsSubset(data, contact.__dict__)

    def test_update_contact_not_belonging_to_user_org(self):
        organization_other = str(uuid.uuid4())
        contact = mfactories.Contact(organization_uuid=organization_other)

        data = {
            'last_name': 'Lynch',
        }
        request = self.factory.post('', json.dumps(data),
                                    content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'update'})
        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 403, response.data)

    def test_update_contact_allows_blank_field(self):
        contact = mfactories.Contact(
            core_user_uuid=self.session['jwt_core_user_uuid'],
            organization_uuid=self.organization_uuid,
            workflowlevel1_uuids=[self.wflvl1])

        data = {
            'first_name': 'David',
            'middle_name': 'Keith',
            'last_name': '',
        }

        request = self.factory.post('', json.dumps(data),
                                    content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'update'})

        response = view(request, pk=contact.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['last_name'], '')

    def test_update_contact_fails_invalid_phone_schema(self):
        contact = mfactories.Contact(
            organization_uuid=self.organization_uuid,
            workflowlevel1_uuids=[self.wflvl1])

        data = {
            'phones': [
                {
                    'type': 'invented',
                    'number': '12345',
                },
                {
                    'type': 'mobile',
                    'number': '67890',
                },
            ],
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'update'})
        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 400)

    def test_update_contact_fails_invalid_customer_id(self):
        mfactories.Contact(
            customer_id='123',
            organization_uuid=self.organization_uuid,
            workflowlevel1_uuids=[self.wflvl1])
        contact = mfactories.Contact(
            customer_id='124',
            organization_uuid=self.organization_uuid,
            workflowlevel1_uuids=[self.wflvl1])

        data = {
            'customer_id': '123',
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'update'})
        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 400)

    def test_update_contact_blank_field_valid(self):
        contact = mfactories.Contact(
            organization_uuid=self.organization_uuid,
            workflowlevel1_uuids=[self.wflvl1])

        data = {
            'middle_name': '',
        }
        request = self.factory.post('', json.dumps(data),
                                    content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = ContactViewSet.as_view({'post': 'update'})

        response = view(request, pk=contact.pk)
        self.assertEqual(response.status_code, 200, response.data)

    def test_update_contacts_anonymoususer(self):
        request = self.factory.post('', {})
        view = ContactViewSet.as_view({'post': 'update'})
        response = view(request)
        self.assertEqual(response.status_code, 403)


class ContactDeleteViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = mfactories.User()
        self.organization_uuid = str(uuid.uuid4())
        self.wflvl1 = str(uuid.uuid4())
        self.wflvl2 = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_core_user_uuid': uuid.uuid4()
        }

    def test_delete_contact(self):
        contact = mfactories.Contact(organization_uuid=self.organization_uuid)
        request = self.factory.delete('')
        request.core_user_uuid = self.user
        request.session = self.session

        view = ContactViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=contact.pk)

        self.assertEquals(response.status_code, 204)
        self.assertRaises(
            Contact.DoesNotExist,
            Contact.objects.get, pk=contact.pk)

    def test_delete_contact_diff_org(self):
        organization_other = str(uuid.uuid4())
        contact = mfactories.Contact(organization_uuid=organization_other)
        request = self.factory.delete('')
        request.user = self.user
        request.session = self.session

        view = ContactViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=contact.pk)

        self.assertEquals(response.status_code, 403)

    def test_delete_contact_diff_org_superuser(self):
        organization_other = str(uuid.uuid4())
        contact = mfactories.Contact(organization_uuid=organization_other)
        request = self.factory.delete('')

        su = mfactories.User()
        su.is_superuser = True
        su.save()

        request.user = su

        view = ContactViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=contact.pk)

        self.assertEquals(response.status_code, 204)

    def test_delete_contact_anonymous_user(self):
        contact = mfactories.Contact(organization_uuid=self.organization_uuid)
        request = self.factory.delete('')

        view = ContactViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=contact.pk)

        self.assertEquals(response.status_code, 403)
