from collections import OrderedDict
from datetime import datetime
import json
import re
import uuid

from django.conf import settings
from django.test import TestCase
import pytz
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory
from django.core import mail

from . import model_factories as mfactories
from contact.tests import model_factories as contact_mfactories
from ..models import Appointment, AppointmentNotification
from ..views import AppointmentViewSet, AppointmentNotificationViewSet


class AppointmentListViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = contact_mfactories.User()
        self.user_uuid = uuid.uuid4()
        self.organization_uuid = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_user_uuid': self.user_uuid
        }

    def test_list_empty(self):
        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, OrderedDict(
            [('next', None), ('previous', None), ('results', [])]))

    def test_list_appointments(self):
        contact_uuid = str(uuid.uuid4())
        siteprofile_uuid = str(uuid.uuid4())
        wflvl2_uuid = uuid.uuid4()
        mfactories.Appointment(
            name='John Tester',
            siteprofile_uuid=siteprofile_uuid,
            contact_uuid=contact_uuid,
            organization_uuid=self.organization_uuid,
            workflowlevel2_uuids=[wflvl2_uuid]
        )

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

        appointment_data = response.data['results'][0]
        self.assertTrue('id' in appointment_data)
        self.assertEqual(appointment_data['name'], 'John Tester')
        self.assertEqual(appointment_data['workflowlevel2_uuids'],
                         [str(wflvl2_uuid)])
        self.assertEqual(appointment_data['siteprofile_uuid'],
                         str(siteprofile_uuid))
        self.assertEqual(appointment_data['contact_uuid'], contact_uuid)

    def test_list_appointments_other_user_same_org(self):
        user_other = uuid.uuid4()
        contact_uuid = str(uuid.uuid4())
        wflvl2_uuid = uuid.uuid4()
        mfactories.Appointment(
            owner=user_other,
            name='John Tester',
            contact_uuid=contact_uuid,
            organization_uuid=self.organization_uuid,
            workflowlevel2_uuids=[wflvl2_uuid]
        )

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_appointments_other_user_diff_org(self):
        user_other = uuid.uuid4()

        contact_uuid = str(uuid.uuid4())
        mfactories.Appointment(
            owner=user_other,
            name='John Tester',
            contact_uuid=contact_uuid,
            organization_uuid=uuid.uuid4()
        )

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

    def test_list_appointments_filter_by_contactuuid(self):
        mfactories.Appointment(name='Other appointment')
        contact_uuid = str(uuid.uuid4())
        mfactories.Appointment(
            name='Appointment 0',
            contact_uuid=contact_uuid,
            organization_uuid=self.organization_uuid
        )
        mfactories.Appointment(
            name='Appointment 1',
            contact_uuid=contact_uuid,
            organization_uuid=self.organization_uuid
        )
        mfactories.Appointment(
            name='Appointment 2',
            contact_uuid=uuid.uuid4(),
            organization_uuid=self.organization_uuid
        )

        request = self.factory.get('?contact_uuid={}'.format(contact_uuid))
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

        appointment_data = response.data['results'][0]
        self.assertEqual(appointment_data['contact_uuid'], contact_uuid)
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 0')
        self.assertEqual(response.data['results'][1]['name'], 'Appointment 1')

    def test_list_appointments_filter_by_owner_me(self):
        user_other = uuid.uuid4()
        contact_uuid = str(uuid.uuid4())
        mfactories.Appointment(
            name='Appointment 0',
            contact_uuid=contact_uuid,
            owner=user_other,
            organization_uuid=self.organization_uuid
        )
        mfactories.Appointment(
            name='Appointment 1',
            contact_uuid=contact_uuid,
            owner=user_other,
            organization_uuid=self.organization_uuid
        )
        mfactories.Appointment(
            name='Appointment 2',
            contact_uuid=contact_uuid,
            owner=self.session['jwt_user_uuid'],
            organization_uuid=self.organization_uuid
        )

        request = self.factory.get('?owner=me')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 2')

    def test_list_appointments_filter_by_owner_other(self):
        user_other = uuid.uuid4()
        contact_uuid = str(uuid.uuid4())
        mfactories.Appointment(
            name='Appointment 0',
            contact_uuid=contact_uuid,
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid
        )
        mfactories.Appointment(
            name='Appointment 1',
            contact_uuid=contact_uuid,
            owner=user_other,
            organization_uuid=self.organization_uuid
        )

        request = self.factory.get('?owner={}'.format(user_other))
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 1')

    def test_list_appointments_filter_by_owner_not_valid_uuid(self):
        request = self.factory.get('?owner=abc')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         ['owner field can only have value "me" or a valid '
                          'User UUID'])

    def test_list_appointments_filter_by_wflvl2(self):
        wflvl2_uuid = uuid.uuid4()
        mfactories.Appointment(
            name='Appointment 0',
            contact_uuid=str(uuid.uuid4()),
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            workflowlevel2_uuids=[wflvl2_uuid]
        )

        request = self.factory.get('?workflowlevel2_uuid={}'.format(
            wflvl2_uuid))
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 0')

    def test_list_appointments_filter_by_unexisting_wflvl2(self):
        wflvl2_uuid = uuid.uuid4()
        mfactories.Appointment(
            name='Appointment 0',
            contact_uuid=str(uuid.uuid4()),
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            workflowlevel2_uuids=[wflvl2_uuid]
        )

        request = self.factory.get('?workflowlevel2_uuid={}'.format(
                                   uuid.uuid4()))
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

    def test_list_appointments_filter_by_invalid_wflvl2(self):
        wflvl2_uuid = uuid.uuid4()
        mfactories.Appointment(
            name='Appointment 0',
            contact_uuid=str(uuid.uuid4()),
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            workflowlevel2_uuids=[wflvl2_uuid]
        )

        request = self.factory.get('?workflowlevel2_uuid=abc')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 400)

    def test_list_appointments_ordering(self):
        mfactories.Appointment(
            name='Other appointment',
            organization_uuid=self.organization_uuid,
        )
        contact_uuid = str(uuid.uuid4())
        mfactories.Appointment(
            name='Appointment 0',
            contact_uuid=contact_uuid,
            organization_uuid=self.organization_uuid,
        )
        mfactories.Appointment(
            name='Appointment 1',
            contact_uuid=contact_uuid,
            organization_uuid=self.organization_uuid,
        )
        mfactories.Appointment(
            name='Appointment 2',
            contact_uuid=contact_uuid,
            organization_uuid=self.organization_uuid,
        )

        request = self.factory.get('?ordering=-id')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 4)

        appointment_data = response.data['results'][0]
        self.assertEqual(appointment_data['contact_uuid'], contact_uuid)
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 2')
        self.assertEqual(response.data['results'][1]['name'], 'Appointment 1')
        self.assertEqual(response.data['results'][2]['name'], 'Appointment 0')

    def test_list_appointments_anonymoususer(self):
        request_get = self.factory.get('')
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request_get)
        self.assertEqual(response.status_code, 403)

    def test_paginate_no_results(self):
        request = self.factory.get('?paginate=true&page_size=1')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)
        self.assertIsNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    def test_paginate_and_denormalize(self):
        contact = contact_mfactories.Contact(
            first_name='Kamasi', last_name='Washington')
        for i in range(0, 2):
            wflvl2_uuid = uuid.uuid4()
            mfactories.Appointment(
                name='John Tester',
                contact_uuid=contact.uuid,
                organization_uuid=self.organization_uuid,
                workflowlevel2_uuids=[wflvl2_uuid]
            )

        request = self.factory.get(
            '?paginate=true&page_size=1&denormalize=true')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['contact']['first_name'],
                         'Kamasi')
        self.assertEqual(response.data['results'][0]['contact']['last_name'],
                         'Washington')
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    def test_paginate_large_result_sets(self):
        contact_uuid = str(uuid.uuid4())

        for i in range(0, 32):
            wflvl2_uuid = uuid.uuid4()
            mfactories.Appointment(
                name='John Tester',
                contact_uuid=contact_uuid,
                organization_uuid=self.organization_uuid,
                workflowlevel2_uuids=[wflvl2_uuid]
            )

        request = self.factory.get('?paginate=true')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 30)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

        m = re.search('=(.*)&', response.data['next'])
        cursor = m.group(1)

        page2_request = self.factory.get('?cursor={}&paginate=true'.format(
            cursor))
        page2_request.user = self.user
        page2_request.session = self.session
        page2_response = view(page2_request)
        self.assertEqual(page2_response.status_code, 200)
        self.assertEqual(len(page2_response.data['results']), 2)
        self.assertIsNone(page2_response.data['next'])
        self.assertIsNotNone(page2_response.data['previous'])

    def test_paginate_large_result_sets_max_size(self):
        contact_uuid = str(uuid.uuid4())

        for i in range(0, 102):
            wflvl2_uuid = uuid.uuid4()
            mfactories.Appointment(
                name='John Tester',
                contact_uuid=contact_uuid,
                organization_uuid=self.organization_uuid,
                workflowlevel2_uuids=[wflvl2_uuid]
            )

        request = self.factory.get('?paginate=true&page_size=100')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 100)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

        m = re.search('=(.*)&', response.data['next'])
        cursor = m.group(1)

        page2_request = self.factory.get('?cursor={}&paginate=true'.format(
            cursor))
        page2_request.user = self.user
        page2_request.session = self.session
        page2_response = view(page2_request)
        self.assertEqual(page2_response.status_code, 200)
        self.assertEqual(len(page2_response.data['results']), 2)
        self.assertIsNone(page2_response.data['next'])
        self.assertIsNotNone(page2_response.data['previous'])

    def test_list_appointments_filter_by_invitee_me(self):
        user_other = uuid.uuid4()
        contact_uuid = str(uuid.uuid4())
        mfactories.Appointment(
            name='Appointment 0',
            contact_uuid=contact_uuid,
            owner=user_other,
            organization_uuid=self.organization_uuid,
            invitee_uuids=[contact_uuid],
        )
        mfactories.Appointment(
            name='Appointment 1',
            contact_uuid=contact_uuid,
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            invitee_uuids=[self.user_uuid],
        )

        request = self.factory.get('?invitee=me')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 1')

    def test_list_appointments_filter_by_invitee_uuid(self):
        user_other = uuid.uuid4()
        contact_uuid = str(uuid.uuid4())
        mfactories.Appointment(
            name='Appointment 0',
            contact_uuid=contact_uuid,
            owner=user_other,
            organization_uuid=self.organization_uuid,
            invitee_uuids=[contact_uuid],
        )
        mfactories.Appointment(
            name='Appointment 1',
            contact_uuid=contact_uuid,
            owner=user_other,
            organization_uuid=self.organization_uuid,
            invitee_uuids=[user_other],
        )

        request = self.factory.get('?invitee={}'.format(user_other))

        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 1')

    def test_list_appointments_filter_by_start_date_gte(self):
        mfactories.Appointment(
            name='Appointment 0',
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            start_date=datetime(2017, 1, 1, 12, 30, tzinfo=pytz.UTC),
            end_date=datetime(2017, 1, 1, 14, 30, tzinfo=pytz.UTC),
        )
        mfactories.Appointment(
            name='Appointment 1',
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            start_date=datetime(2018, 1, 28, 12, 30, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 28, 14, 30, tzinfo=pytz.UTC),
        )

        request = self.factory.get('?start_date_gte=2018-1-28')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 1')

    def test_list_appointments_filter_by_start_date_lte(self):
        mfactories.Appointment(
            name='Appointment 0',
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            start_date=datetime(2017, 1, 1, 12, 30, tzinfo=pytz.UTC),
            end_date=datetime(2017, 1, 1, 14, 30, tzinfo=pytz.UTC),
        )
        mfactories.Appointment(
            name='Appointment 1',
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            start_date=datetime(2018, 1, 28, 12, 30, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 28, 14, 30, tzinfo=pytz.UTC),
        )

        request = self.factory.get('?start_date_lte=2017-1-1')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 0')

    def test_list_appointments_filter_by_start_date_gte_and_lte(self):
        mfactories.Appointment(
            name='Appointment 0',
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            start_date=datetime(2017, 1, 1, 12, 30, tzinfo=pytz.UTC),
            end_date=datetime(2017, 1, 1, 14, 30, tzinfo=pytz.UTC),
        )
        mfactories.Appointment(
            name='Appointment 1',
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid,
            start_date=datetime(2018, 1, 28, 12, 30, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 28, 14, 30, tzinfo=pytz.UTC),
        )

        request = self.factory.get(
            '?start_date_gte=2017-1-1&start_date_lte=2018-1-28')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)

        request = self.factory.get(
            '?start_date_gte=2017-1-1&start_date_lte=2018-1-27')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1,
                         response.data['results'])
        self.assertEqual(response.data['results'][0]['name'], 'Appointment 0')

    def test_list_appointments_denormalized(self):
        contact = contact_mfactories.Contact()
        wflvl2_uuid = uuid.uuid4()
        mfactories.Appointment(
            name='John Tester',
            contact_uuid=contact.uuid,
            organization_uuid=self.organization_uuid,
            workflowlevel2_uuids=[wflvl2_uuid]
        )

        request = self.factory.get('?denormalize=true')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'list'})
        response = view(request)

        appointment_data = response.data['results'][0]

        self.assertTrue('id' in appointment_data)
        self.assertEqual(appointment_data['name'], 'John Tester')
        self.assertEqual(appointment_data['workflowlevel2_uuids'][0],
                         str(wflvl2_uuid))
        self.assertEqual(appointment_data['contact_uuid'], str(contact.uuid))
        self.assertEqual(appointment_data['contact']['first_name'],
                         contact.first_name)
        self.assertEqual(appointment_data['contact']['middle_name'],
                         contact.middle_name)
        self.assertEqual(appointment_data['contact']['last_name'],
                         contact.last_name)


class AppointmentRetrieveViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = contact_mfactories.User()
        self.user_uuid = uuid.uuid4()
        self.organization_uuid = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_user_uuid': self.user_uuid
        }

    def test_retrieve_appointment_owner(self):
        contact_uuid = str(uuid.uuid4())
        siteprofile_uuid = str(uuid.uuid4())
        wflvl2_uuid = uuid.uuid4()
        appointment = mfactories.Appointment(
            name='John Tester',
            owner=self.user_uuid,
            siteprofile_uuid=siteprofile_uuid,
            contact_uuid=contact_uuid,
            organization_uuid=self.organization_uuid,
            workflowlevel2_uuids=[str(wflvl2_uuid)]
        )
        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=appointment.pk)
        self.assertEqual(response.status_code, 200)

        appointment_data = appointment.__dict__

        for field in ('owner', '_state'):
            del appointment_data[field]

        for field in ('siteprofile_uuid', 'contact_uuid',
                      'organization_uuid', 'uuid'):
            appointment_data[field] = str(appointment_data[field])

        data = response.data

        local = pytz.timezone(settings.TIME_ZONE)
        start_date_naive = datetime.strptime(
            data['start_date'], "%Y-%m-%dT%H:%M:%S+01:00")
        start_date_local = local.localize(start_date_naive, is_dst=None)
        data['start_date'] = start_date_local.astimezone(pytz.utc)

        end_date_naive = datetime.strptime(
            data['end_date'], "%Y-%m-%dT%H:%M:%S+01:00")
        end_date_local = local.localize(end_date_naive, is_dst=None)
        data['end_date'] = end_date_local.astimezone(pytz.utc)

        self.assertDictContainsSubset(appointment_data, data)

    def test_retrieve_appointment_not_owner_same_org(self):
        other_user_uuid = uuid.uuid4()
        appointment = mfactories.Appointment(
            owner=other_user_uuid,
            organization_uuid=self.organization_uuid
        )

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=appointment.pk)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_appointment_not_owner_diff_org(self):
        other_org_uuid = uuid.uuid4()
        other_user_uuid = uuid.uuid4()
        appointment = mfactories.Appointment(
            owner=other_user_uuid,
            organization_uuid=other_org_uuid
        )

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=appointment.pk)
        self.assertEqual(response.status_code, 403)

    def test_retrieve_appointment_not_owner_diff_org_empty(self):
        other_user_uuid = uuid.uuid4()
        appointment = mfactories.Appointment(owner=other_user_uuid)

        request = self.factory.get('')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=appointment.pk)

        self.assertEqual(response.status_code, 403)

    def test_retrieve_appointment_anonymoususer(self):
        request_get = self.factory.get('')
        view = AppointmentViewSet.as_view({'get': 'retrieve'})
        response = view(request_get)
        self.assertEqual(response.status_code, 403)

    def test_retrieve_appointment_denormalized(self):
        contact = contact_mfactories.Contact()
        invitee_user_uuid = uuid.uuid4()

        appointment = mfactories.Appointment(
            name='John Tester',
            contact_uuid=contact.uuid,
            owner=self.user_uuid,
            invitee_uuids=[invitee_user_uuid],
            organization_uuid=self.organization_uuid
        )

        request = self.factory.get('?denormalize=true')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=appointment.pk)
        self.assertEqual(response.status_code, 200)

        appointment_data = appointment.__dict__
        appointment_data['invitee_uuids'][0] = str(
            appointment_data['invitee_uuids'][0])

        for field in ('owner', '_state'):
            del appointment_data[field]

        for field in ('contact_uuid', 'organization_uuid', 'uuid'):
            appointment_data[field] = str(appointment_data[field])

        data = response.data

        local = pytz.timezone(settings.TIME_ZONE)
        start_date_naive = datetime.strptime(
            data['start_date'], "%Y-%m-%dT%H:%M:%S+01:00")
        start_date_local = local.localize(start_date_naive, is_dst=None)
        data['start_date'] = start_date_local.astimezone(pytz.utc)

        end_date_naive = datetime.strptime(
            data['end_date'], "%Y-%m-%dT%H:%M:%S+01:00")
        end_date_local = local.localize(end_date_naive, is_dst=None)
        data['end_date'] = end_date_local.astimezone(pytz.utc)

        self.assertDictContainsSubset(appointment_data, data)
        self.assertEqual(data['contact_uuid'], str(contact.uuid))
        self.assertEqual(data['contact']['first_name'],
                         contact.first_name)
        self.assertEqual(data['contact']['middle_name'],
                         contact.middle_name)
        self.assertEqual(data['contact']['last_name'],
                         contact.last_name)


class AppointmentCreateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = contact_mfactories.User()
        self.user_uuid = uuid.uuid4()
        self.organization_uuid = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_user_uuid': self.user_uuid
        }

    def test_create_appointment_minimal(self):
        data = {
            'name': 'Max Mustermann',
            'start_date': datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            'end_date': datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            'address': 'Teststreet 123',
            'type': ['Test Type']
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

        appointment = Appointment.objects.get(id=response.data['id'])
        self.assertEqual(appointment.owner, self.user_uuid)
        self.assertEqual(appointment.name, data['name'])
        self.assertEqual(appointment.start_date, data['start_date'])
        self.assertEqual(appointment.end_date, data['end_date'])

    def test_create_appointment(self):
        wflvl2_uuid = uuid.uuid4()
        start_date = datetime(2018, 1, 1, 12, 15)\
            .strftime("%Y-%m-%dT%H:%M:%S+01:00")
        end_date = datetime(2018, 1, 1, 12, 30)\
            .strftime("%Y-%m-%dT%H:%M:%S+01:00")
        invitee_uuids = [uuid.uuid4(), uuid.uuid4()]
        contact_uuid = uuid.uuid4()
        siteprofile_uuid = uuid.uuid4()

        data = {
            'name': 'Max Mustermann',
            'start_date': start_date,
            'end_date': end_date,
            'address': 'Teststreet 123',
            'siteprofile_uuid': str(siteprofile_uuid),
            'invitee_uuids': invitee_uuids,
            'type': ['Test Type'],
            'notes': 'Please help me, youre my only hope',
            'workflowlevel2_uuids': [wflvl2_uuid],
            'contact_uuid': contact_uuid,
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

        appointment = Appointment.objects.get(id=response.data['id'])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(appointment.name, data['name'])
        self.assertEqual(appointment.address, data['address'])
        self.assertEqual(appointment.siteprofile_uuid, siteprofile_uuid)
        self.assertEqual(appointment.invitee_uuids, invitee_uuids)
        self.assertEqual(appointment.notes, data['notes'])
        self.assertEqual(appointment.contact_uuid, data['contact_uuid'])
        self.assertEqual(appointment.workflowlevel2_uuids,
                         data['workflowlevel2_uuids'])

        local = pytz.timezone(settings.TIME_ZONE)
        start_date_naive = datetime.strptime(
            data['start_date'], "%Y-%m-%dT%H:%M:%S+01:00")
        start_date_local = local.localize(start_date_naive, is_dst=None)
        self.assertEqual(appointment.start_date, start_date_local)

        start_date_naive = datetime.strptime(
            data['end_date'], "%Y-%m-%dT%H:%M:%S+01:00")
        end_date_local = local.localize(start_date_naive, is_dst=None)
        self.assertEqual(appointment.end_date, end_date_local)

    def test_create_appointment_diff_org_than_user(self):
        start_date = datetime(2018, 1, 1, 12, 15)\
            .strftime("%Y-%m-%dT%H:%M:%S+01:00")
        end_date = datetime(2018, 1, 1, 12, 30)\
            .strftime("%Y-%m-%dT%H:%M:%S+01:00")

        data = {
            'name': 'Max Mustermann',
            'start_date': start_date,
            'end_date': end_date,
            'type': ['Test Type'],
            'address': 'Teststreet 123',
            'organization_uuid': str(uuid.uuid4()),
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'organization_uuid': [
            "The Organization cannot be different than user's organization"]})

    def test_create_appointment_empty_org(self):
        start_date = datetime(2018, 1, 1, 12, 15)\
            .strftime("%Y-%m-%dT%H:%M:%S+01:00")
        end_date = datetime(2018, 1, 1, 12, 30)\
            .strftime("%Y-%m-%dT%H:%M:%S+01:00")

        data = {
            'name': 'Max Mustermann',
            'start_date': start_date,
            'end_date': end_date,
            'type': ['Test Type'],
            'address': 'Teststreet 123',
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['organization_uuid'],
                         str(self.organization_uuid))

    def test_create_appointment_anonymoususer(self):
        request = self.factory.post('', {})
        view = AppointmentViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_create_appointment_fails_empty_field(self):
        data = {
            'name': '',
            'start_date': datetime(2018, 1, 1, 12, 15),
            'end_date': datetime(2018, 1, 1, 12, 30),
            'address': 'Teststreet 123',
            'type': ['Test Type']
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)

    def test_create_appointment_fails_invalid_date_schema(self):
        data = {
            'name': '',
            'start_date': '2018.1.2.',
            'end_date': datetime(2018, 1, 1, 12, 30),
            'address': 'Teststreet 123',
            'type': ['Test Type']
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)

    def test_create_appointment_fails_date_range(self):
        data = {
            'name': '',
            'start_date': datetime(2018, 1, 1, 12, 15),
            'end_date': datetime(2018, 1, 1, 11, 30),
            'address': 'Teststreet 123',
            'type': ['Test Type']
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)

    def test_create_appointment_fails_empty_type_array(self):
        data = {
            'name': 'Max Mustermann',
            'start_date': datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            'end_date': datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            'address': 'Teststreet 123',
            'type': [],
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {'type': ['type must be an array of one or more string elements']}
        )


class AppointmentUpdateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = contact_mfactories.User()
        self.user_uuid = uuid.uuid4()
        self.organization_uuid = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_user_uuid': self.user_uuid
        }

    def test_update_appointment(self):
        appointment = mfactories.Appointment(
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid
        )

        invitee_uuids = [uuid.uuid4(), uuid.uuid4()]
        contact_uuid = str(uuid.uuid4())
        siteprofile_uuid = uuid.uuid4()
        data = {
            'name': 'Max Mustermann',
            'start_date': datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            'siteprofile_uuid': str(siteprofile_uuid),
            'invitee_uuids': invitee_uuids,
            'notes': 'Please help me, youre my only hope',
            'contact_uuid': contact_uuid,
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'update'})
        response = view(request, pk=appointment.pk)
        self.assertEqual(response.status_code, 200)

        appointment = Appointment.objects.get(id=response.data['id'])
        self.assertEqual(appointment.invitee_uuids, invitee_uuids)
        self.assertEqual(appointment.siteprofile_uuid, siteprofile_uuid)

    def test_update_appointment_json(self):
        appointment = mfactories.Appointment(
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid
        )

        contact_uuid = uuid.uuid4()
        wflvl2_uuid = uuid.uuid4()

        data = {
            'name': 'Max Mustermann',
            'notes': 'Please help me, youre my only hope',
            'contact_uuid': str(contact_uuid),
            'workflowlevel2_uuids': [str(wflvl2_uuid)]
        }

        request = self.factory.post('', json.dumps(data),
                                    content_type='application/json')
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'update'})
        response = view(request, pk=appointment.pk)

        self.assertEqual(response.status_code, 200)
        appointment = Appointment.objects.get(id=response.data['id'])
        self.assertEqual(appointment.contact_uuid, contact_uuid)
        self.assertEqual(list(appointment.workflowlevel2_uuids), [wflvl2_uuid])

    def test_update_appointment_superuser(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        other_org_uuid = uuid.uuid4()
        appointment = mfactories.Appointment(
            owner=self.user_uuid,
            organization_uuid=other_org_uuid
        )

        data = {
            'name': 'Other Name',
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'update'})
        response = view(request, pk=appointment.pk)

        self.assertEqual(response.status_code, 200)

    def test_update_appointment_diff_org(self):
        other_org_uuid = uuid.uuid4()
        other_user_uuid = uuid.uuid4()
        appointment = mfactories.Appointment(
            owner=other_user_uuid,
            organization_uuid=other_org_uuid,
            workflowlevel2_uuids=[uuid.uuid4()]
        )

        data = {
            'name': 'Test Name',
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'update'})
        response = view(request, pk=appointment.pk)
        self.assertEqual(response.status_code, 403)

    def test_update_appointment_fails_blank_field(self):
        appointment = mfactories.Appointment(
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid
        )

        data = {
            'name': '',
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentViewSet.as_view({'post': 'update'})
        response = view(request, pk=appointment.pk)
        self.assertEqual(response.status_code, 400)

    def test_update_appointment_fails_invalid_date_schema(self):
        appointment = mfactories.Appointment(
            owner=self.user_uuid,
            organization_uuid=self.organization_uuid
        )

        data = {
            'end_date': '2018.1.1.'
        }
        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session

        view = AppointmentViewSet.as_view({'post': 'update'})
        response = view(request, pk=appointment.pk)
        self.assertEqual(response.status_code, 400)

    def test_update_appointment_anonymoususer_forbidden(self):
        request = self.factory.post('', {})
        view = AppointmentViewSet.as_view({'post': 'update'})
        response = view(request)
        self.assertEqual(response.status_code, 403)


class AppointmentNotificationCreateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = contact_mfactories.User()
        self.user_uuid = uuid.uuid4()
        self.organization_uuid = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_user_uuid': self.user_uuid
        }

    def test_create_appointment_notification_minimal(self):
        appointment = mfactories.Appointment()

        data = {
            'recipient': 'test@example.com',
            'appointment': reverse('appointment-detail',
                                   kwargs={'pk': appointment.pk})
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentNotificationViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

        notification = AppointmentNotification.objects.get(
            id=response.data['id'])
        self.assertIsNotNone(notification.subject)
        self.assertIsNotNone(notification.message)

    def test_create_appointment_notification(self):
        appointment = mfactories.Appointment()

        data = {
            'recipient': 'test@example.com',
            'message': 'This is a new message',
            'subject': 'New Subject',
            'appointment': reverse('appointment-detail',
                                   kwargs={'pk': appointment.pk}),
            'org_phone': '+123 456 78',
            'org_name': 'Your org'
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentNotificationViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

        notification = AppointmentNotification.objects.get(
            id=response.data['id'])
        self.assertIsNotNone(notification.subject)
        self.assertIsNotNone(notification.message)

    def test_create_appointment_notification_anonymoususer(self):
        request = self.factory.post('', {})
        view = AppointmentNotificationViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_create_appointment_notification_fails_no_recipient(self):
        data = {
            'recipient': 'test@example.org'
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentNotificationViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)

    def test_create_appointment_send_immmediately(self):
        appointment = mfactories.Appointment()

        data = {
            'recipient': 'test@example.com',
            'appointment': reverse('appointment-detail',
                                   kwargs={'pk': appointment.pk}),
            'send_notification': True
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentNotificationViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

        notification = AppointmentNotification.objects.get(
            id=response.data['id'])
        self.assertIsNotNone(notification.subject)
        self.assertIsNotNone(notification.message)
        self.assertEqual(len(mail.outbox), 1)


class AppointmentNotificationRetrieveViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = contact_mfactories.User()
        self.user_uuid = str(uuid.uuid4())
        self.organization_uuid = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_user_uuid': self.user_uuid
        }

    def test_retrieve_appointment_notification_owner(self):
        appointment = mfactories.Appointment(
            owner=self.user_uuid
        )
        appointment_notification = mfactories.AppointmentNotification(
            appointment=appointment
        )
        request = self.factory.get('')
        request.user = self.user
        request.session = self.session

        view = AppointmentNotificationViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=appointment_notification.pk)
        self.assertEqual(response.status_code, 200)

        obj_data = appointment_notification.__dict__
        for field in ('appointment_id', '_state'):
            del obj_data[field]

        data = response.data
        self.assertDictContainsSubset(obj_data, data)

    def test_retrieve_appointment_notification_fails(self):
        appointment = mfactories.Appointment()
        appointment_notification = mfactories.AppointmentNotification(
            appointment=appointment)
        request = self.factory.get('')

        request.user = self.user
        request.session = self.session

        view = AppointmentNotificationViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=appointment_notification.pk)
        self.assertEqual(response.status_code, 403)

    def test_retrieve_appointment_notification_anonymoususer(self):
        request_get = self.factory.get('')
        view = AppointmentNotificationViewSet.as_view({'get': 'retrieve'})
        response = view(request_get)
        self.assertEqual(response.status_code, 403)


class AppointmentNotificationUpdateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = contact_mfactories.User()
        self.user_uuid = uuid.uuid4()
        self.organization_uuid = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_user_uuid': self.user_uuid
        }

    def test_update_appointment_notification(self):
        appointment = mfactories.Appointment(
            organization_uuid=self.organization_uuid
        )
        appointment_notification = mfactories.AppointmentNotification(
            appointment=appointment
        )

        data = {
            'recipient': 'test@example.com',
            'message': 'This is a new message',
            'subject': 'New Subject',
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentNotificationViewSet.as_view({'post': 'update'})
        response = view(request, pk=appointment_notification.pk)
        self.assertEqual(response.status_code, 200)

        saved_obj = AppointmentNotification.objects.get(id=response.data['id'])
        self.assertEqual(data['message'], saved_obj.message)

    def test_update_appointment_notification_fails_blank_field(self):
        appointment = mfactories.Appointment(
            organization_uuid=self.organization_uuid
        )
        appointment_notification = mfactories.AppointmentNotification(
            appointment=appointment
        )

        data = {
            'recipient': '',
            'appointment':
                reverse(
                    'appointment-detail',
                    kwargs={'pk': appointment_notification.appointment.pk}),
        }

        request = self.factory.post('', data)
        request.user = self.user
        request.session = self.session
        view = AppointmentNotificationViewSet.as_view({'post': 'update'})
        response = view(request, pk=appointment_notification.pk)
        self.assertEqual(response.status_code, 400)

    def test_update_appointment_notification_anonymoususer_forbidden(self):
        request = self.factory.post('', {})
        view = AppointmentNotificationViewSet.as_view({'post': 'update'})
        response = view(request)
        self.assertEqual(response.status_code, 403)
