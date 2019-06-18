from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from . import model_factories as mfactories
from ..serializers import AppointmentSerializer, AppointmentDrivingTimeSerializer


class AppointmentSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_contains_expected_fields(self):
        appointment = mfactories.Appointment()
        request = self.factory.get('/')
        serializer_context = {
            'request': Request(request),
        }
        serializer = AppointmentSerializer(instance=appointment,
                                           context=serializer_context)
        data = serializer.data
        keys = [
            'id',
            'contact',
            'notes',
            'driving_times',
            'uuid',
            'name',
            'start_date',
            'end_date',
            'type',
            'address',
            'siteprofile_uuid',
            'invitee_uuids',
            'organization_uuid',
            'workflowlevel2_uuids',
            'contact_uuid',
            'summary',
        ]
        self.assertEqual(set(data.keys()), set(keys))


class AppointmentDrivingTimeSerializerTest(TestCase):

    def test_contains_expected_fields(self):
        driving_time = mfactories.AppointmentDrivingTime()
        serializer = AppointmentDrivingTimeSerializer(instance=driving_time)
        data = serializer.data
        keys = [
            'uuid',
            'time',
            'distance',
            'appointment',
            'time_point',
        ]
        self.assertEqual(set(data.keys()), set(keys))
