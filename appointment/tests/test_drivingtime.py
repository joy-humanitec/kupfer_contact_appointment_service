import uuid
from unittest import TestCase

from rest_framework.test import APIRequestFactory

from appointment.views import AppointmentDrivingTimeViewSet
from . import model_factories as mfactories


class AppointmentDrivingTimeViewsBaseTest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.core_user_uuid = uuid.uuid4()
        self.organization_uuid = str(uuid.uuid4())
        self.session = {
            'jwt_organization_uuid': self.organization_uuid,
            'jwt_username': 'Test User',
            'jwt_core_user_uuid': self.core_user_uuid
        }


class AppointmentDrivingTimeViewsCreateTest(AppointmentDrivingTimeViewsBaseTest):

    def test_create_driving_time(self):
        appointment = mfactories.Appointment(
            owner=self.core_user_uuid,
            organization_uuid=self.organization_uuid,
        )
        data = {
            'appointment': str(appointment.pk),
            'distance': 2.50,
            'time': 3,
        }

        request = self.factory.post('', data)
        request.session = self.session

        view = AppointmentDrivingTimeViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["distance"], "2.50")
        self.assertEqual(response.data["time"], 3)


class AppointmentDrivingTimeViewsRetrieveTest(AppointmentDrivingTimeViewsBaseTest):

    def test_retrieve_driving_time(self):
        appointment = mfactories.Appointment(
            owner=self.core_user_uuid,
            organization_uuid=self.organization_uuid,
        )
        driving_time = mfactories.AppointmentDrivingTime(appointment=appointment)

        request = self.factory.get('')
        request.session = self.session

        view = AppointmentDrivingTimeViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=driving_time.pk)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_driving_time_permission_failed(self):
        appointment = mfactories.Appointment(
            owner=self.core_user_uuid,
            organization_uuid=str(uuid.uuid4()),
        )
        driving_time = mfactories.AppointmentDrivingTime(appointment=appointment)

        request = self.factory.get('')
        request.session = self.session

        view = AppointmentDrivingTimeViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=driving_time.pk)
        self.assertEqual(response.status_code, 403)


class AppointmentDrivingTimeViewsUpdateTest(AppointmentDrivingTimeViewsBaseTest):

    def test_update_driving_time(self):
        appointment = mfactories.Appointment(
            owner=self.core_user_uuid,
            organization_uuid=self.organization_uuid,
        )
        driving_time = mfactories.AppointmentDrivingTime(
            appointment=appointment,
            distance=1.0,
            time=1
        )

        self.assertEqual(appointment.driving_times.all()[0].distance, 1.0)

        data = {
            "distance": 2.5,
            "time": '2',
        }

        request = self.factory.patch('', data)
        request.session = self.session

        view = AppointmentDrivingTimeViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=driving_time.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["distance"], "2.50")
        self.assertEqual(response.data["time"], 2)


class AppointmentDrivingTimeViewsDeleteTest(AppointmentDrivingTimeViewsBaseTest):

    def test_delete_driving_time(self):
        appointment = mfactories.Appointment(
            owner=self.core_user_uuid,
            organization_uuid=self.organization_uuid,
        )
        driving_time = mfactories.AppointmentDrivingTime(appointment=appointment)

        self.assertEqual(appointment.driving_times.count(), 1)

        request = self.factory.delete('')
        request.session = self.session

        view = AppointmentDrivingTimeViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=driving_time.pk)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(appointment.driving_times.count(), 0)

    def test_delete_driving_time_permission_denied(self):
        appointment = mfactories.Appointment(
            owner=self.core_user_uuid,
            organization_uuid=self.organization_uuid,
        )
        driving_time = mfactories.AppointmentDrivingTime(appointment=appointment)

        self.assertEqual(appointment.driving_times.count(), 1)

        request = self.factory.delete('')
        # no session

        view = AppointmentDrivingTimeViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=driving_time.pk)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(appointment.driving_times.count(), 1)
