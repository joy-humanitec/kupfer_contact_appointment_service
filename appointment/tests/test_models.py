from datetime import datetime
import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.core import mail
import pytz

from ..models import Appointment, AppointmentNotification
from . import model_factories as mfactories


class AppointmentTest(TestCase):
    def setUp(self):
        self.user_uuid = uuid.uuid4()

    def assertRaisesWithMessage(self, exc, msg, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.assertFail()
        except exc as inst:
            self.assertIn(msg, inst.messages)

    def assertRaisesWithMessageDict(self, exc, msg, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.assertFail()
        except exc as inst:
            self.assertEqual(msg, inst.message_dict)

    def test_appointment_save_required_fields(self):
        appointment = Appointment.objects.create(
            owner=self.user_uuid,
            name="Test Name 1",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )

        appointment_db = Appointment.objects.get(pk=appointment.pk)
        self.assertEqual(appointment_db.name, "Test Name 1")

    def test_appointment_save_all_fields(self):
        appointment = Appointment.objects.create(
            owner=self.user_uuid,
            name="Test Name 2",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            invitee_uuids=[uuid.uuid4(), uuid.uuid4()],
            notes="Test note",
            type=["Test Type"],
            contact_uuid=str(uuid.uuid4())
        )

        appointment_db = Appointment.objects.get(pk=appointment.pk)
        self.assertEqual(appointment_db.name, "Test Name 2")

    def test_appointment_save_fails_missing_owner(self):
        appointment = Appointment(
            name="Test Name 2",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )

        self.assertRaises(ValidationError, appointment.save)

    def test_appointment_save_fails_missing_name(self):
        appointment = Appointment(
            owner=self.user_uuid,
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )

        self.assertRaises(ValidationError, appointment.save)

    def test_appointment_save_fails_missing_start_date(self):
        appointment = Appointment(
            owner=self.user_uuid,
            name="Test Name 2",
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )

        self.assertRaisesWithMessage(
            ValidationError, 'start_date is not of type datetime.',
            appointment.save)

    def test_appointment_save_fails_missing_end_date(self):
        appointment = Appointment(
            owner=self.user_uuid,
            name="Test Name 2",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )

        self.assertRaisesWithMessage(
            ValidationError, 'end_date is not of type datetime.',
            appointment.save)

    def test_appointment_save_fails_missing_address(self):
        appointment = Appointment(
            owner=self.user_uuid,
            name="Test Name 2",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            type=["Test Type"]
        )

        self.assertRaisesWithMessageDict(
            ValidationError, {'address': ['This field cannot be blank.']},
            appointment.save)

    def test_appointment_save_fails_missing_type(self):
        appointment = Appointment(
            owner=self.user_uuid,
            name="Test Name 2",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
        )

        self.assertRaisesWithMessageDict(
            ValidationError, {'type': ['This field cannot be null.']},
            appointment.save)

    def test_appointment_save_fails_wrong_date_format_start_date(self):
        appointment = Appointment(
            owner=self.user_uuid,
            name="Test Name 1",
            start_date="2018.1.1",
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )

        self.assertRaises(ValidationError, appointment.save)

    def test_appointment_save_fails_wrong_date_format_end_date(self):
        appointment = Appointment(
            owner=self.user_uuid,
            name="Test Name 1",
            start_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            end_date="2018.1.1",
            address="Teststreet 123",
            type=["Test Type"]
        )

        self.assertRaises(ValidationError, appointment.save)

    def test_appointment_save_fails_impossible_dates(self):
        appointment = Appointment(
            owner=self.user_uuid,
            name="Test Name 1",
            start_date=datetime(2018, 2, 2, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )

        self.assertRaises(ValidationError, appointment.save)

    def test_str_representation(self):
        appointment = Appointment.objects.create(
            owner=self.user_uuid,
            name="Appointment1",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )

        self.assertEqual(str(appointment),
                         'Appointment1 2018-01-01 12:15:00+00:00')


class AppointmentNotificationsTest(TestCase):
    def setUp(self):
        self.appointment = mfactories.Appointment()

    def test_appointment_notification_save_required_fields(self):
        appointment_notification = AppointmentNotification.objects.create(
            recipient='test@example.com',
            appointment=self.appointment,
        )

        saved_obj = AppointmentNotification.objects.get(
            pk=appointment_notification.pk)
        self.assertEqual(saved_obj.recipient, "test@example.com")
        self.assertIsNotNone(saved_obj.message)
        self.assertIsNotNone(saved_obj.subject)

    def test_appointment_notification_save_all_fields(self):
        appointment_notification = AppointmentNotification.objects.create(
            recipient='test2@example.com',
            appointment=self.appointment,
            message='Test Message lorem ipsum',
            subject='Lorem ipsum',
            send_notification=False,
            sent_at=None
        )

        saved_obj = AppointmentNotification.objects.get(
            pk=appointment_notification.pk)
        self.assertEqual(saved_obj.recipient, "test2@example.com")
        self.assertEqual(saved_obj.subject, "Lorem ipsum")

    def test_appointment_notification_save_fails_missing_recipient(self):
        appointment_notification = AppointmentNotification(
            recipient='',
            appointment=self.appointment,
        )

        self.assertRaises(ValidationError, appointment_notification.save)

    def test_appointment_notification_save_fails_wrong_email(self):
        appointment_notification = AppointmentNotification(
            recipient='test',
            appointment=self.appointment,
        )

        self.assertRaises(ValidationError, appointment_notification.save)

    def test_appointment_notification_save_fails_missing_appointment(self):
        appointment_notification = AppointmentNotification(
            recipient='test@example.com',
            appointment=None,
        )

        self.assertRaises(ValidationError, appointment_notification.save)

    def test_appointemnt_notification_sends_email(self):
        appointment_notification = AppointmentNotification.objects.create(
            recipient='test2@example.com',
            appointment=self.appointment,
            message='Test Message lorem ipsum',
            subject='Lorem ipsum',
            send_notification=True,
            sent_at=None
        )

        saved_obj = AppointmentNotification.objects.get(
            pk=appointment_notification.pk)
        self.assertEqual(saved_obj.recipient, "test2@example.com")
        self.assertEqual(saved_obj.subject, "Lorem ipsum")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Lorem ipsum")

    def test_str_representation(self):
        appointment = Appointment.objects.create(
            owner=uuid.uuid4(),
            name="Appointment1",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )
        appointment_notification = AppointmentNotification.objects.create(
            recipient='test@example.com',
            appointment=appointment,
            sent_at=datetime(2017, 12, 21, 12, 15, tzinfo=pytz.UTC)
        )

        self.assertEqual(str(appointment_notification),
                         'Appointment1 2018-01-01 12:15:00+00:00 (2017-12-21 '
                         '12:15:00+00:00)')

    def test_str_representation_date_none(self):
        appointment = Appointment.objects.create(
            owner=uuid.uuid4(),
            name="Appointment1",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Teststreet 123",
            type=["Test Type"]
        )
        appointment_notification = AppointmentNotification.objects.create(
            recipient='test@example.com',
            appointment=appointment,
            sent_at=None
        )

        self.assertEqual(str(appointment_notification),
                         'Appointment1 2018-01-01 12:15:00+00:00 (None)')
