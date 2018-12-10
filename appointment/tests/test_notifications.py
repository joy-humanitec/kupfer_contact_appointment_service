from ..notifications import AppointmentNotificationEMail
from datetime import datetime, timedelta
import uuid

from django.test import TestCase
from django.core import mail

import pytz

from ..models import Appointment, AppointmentNotification
import contact.tests.model_factories as cfactories


class AppointmentNotificationEmailTest(TestCase):
    def setUp(self):
        self.user = cfactories.User()
        self.user_uuid = uuid.uuid4()

    def test_mail(self):
        contact = cfactories.Contact()
        org_name = 'Test org'
        org_phone = '1234 56'

        invitee = uuid.uuid4()

        appointment = Appointment.objects.create(
            owner=self.user_uuid, name="Test Name 2",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Oderberger Straße 16A", invitee_uuids=[invitee],
            notes="Test note", type=["Test Type"],
            contact_uuid=str(contact.uuid)
        )

        appointment_notification = AppointmentNotification.objects.create(
            subject="Test Mail",
            message="Test Body",
            recipient='test@example.com',
            appointment=appointment,
            org_name=org_name,
            org_phone=org_phone
        )

        ap_mail = AppointmentNotificationEMail(appointment_notification)

        ap_mail.notify_recipient()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].body, 'Test Body')

    def test_mail_not_send(self):
        contact = cfactories.Contact()
        org_name = 'Test org'
        org_phone = '1234 56'

        invitee = uuid.uuid4()

        appointment = Appointment.objects.create(
            owner=self.user_uuid, name="Test Name 2",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Oderberger Straße 16A", invitee_uuids=[invitee],
            notes="Test note", type=["Test Type"],
            organization_uuid=uuid.uuid4(),
            contact_uuid=str(contact.uuid)
        )

        appointment_notification = AppointmentNotification.objects.create(
            subject="Test Mail",
            message="Test Body",
            recipient='test@example.com',
            appointment=appointment,
            sent_at=datetime.now(),
            org_name=org_name,
            org_phone=org_phone
        )

        ap_mail = AppointmentNotificationEMail(appointment_notification)

        ap_mail.notify_recipient()

        self.assertEqual(len(mail.outbox), 0)

    def test_message_body_generation(self):
        contact = cfactories.Contact()

        invitee = uuid.uuid4()

        appointment = Appointment.objects.create(
            owner=self.user_uuid, name="Test Name 2",
            start_date=datetime(2018, 1, 1, 12, 15, tzinfo=pytz.UTC),
            end_date=datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC),
            address="Oderberger Straße 16A", invitee_uuids=[invitee],
            notes="Test note", type=["Test Type"],
            organization_uuid=uuid.uuid4(),
            contact_uuid=str(contact.uuid)
        )

        appointment_notification = AppointmentNotification.objects.create(
            subject="Test Mail",
            message="Test Body",
            recipient='test@example.com',
            appointment=appointment,
            sent_at=datetime.now()
        )

        ap_mail = AppointmentNotificationEMail(appointment_notification)

        message = ap_mail.generate_message()[1]

        regex = r'.*{}.*'.format(
            appointment.start_date.strftime('%M:%H'))
        self.assertRegexpMatches(message, regex)
        self.assertEqual(len(mail.outbox), 0)

    def test_message_subject_generation(self):
        contact = cfactories.Contact()
        invitee = uuid.uuid4()

        time_offset = 4
        start_date = datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(
            days=time_offset)
        end_date = start_date + timedelta(hours=2)

        appointment = Appointment.objects.create(
            owner=self.user_uuid, name="Test Name 2",
            start_date=start_date,
            end_date=end_date,
            address="Oderberger Straße 16A", invitee_uuids=[invitee],
            notes="Test note", type=["Test Type"],
            organization_uuid=uuid.uuid4(),
            contact_uuid=str(contact.uuid)
        )

        appointment_notification = AppointmentNotification.objects.create(
            recipient='test@example.com',
            appointment=appointment,
            sent_at=datetime.now()
        )

        ap_mail = AppointmentNotificationEMail(appointment_notification)

        subject = ap_mail.generate_message()[0]

        regex = r'Erinnerung an Ihren Termin in {} Tagen.*'.format(
            time_offset-1)
        self.assertRegexpMatches(subject, regex)
        self.assertEqual(len(mail.outbox), 0)
