from datetime import datetime
import pytz
import uuid

from factory import DjangoModelFactory, Iterator, SubFactory

from ..models import Appointment as AppointmentM
from ..models import AppointmentNotification as AppointmentNotificationM


class Appointment(DjangoModelFactory):
    class Meta:
        model = AppointmentM

    owner = uuid.uuid4()
    name = Iterator(['David', 'Nina'])
    start_date = datetime(2018, 1, 1, 12, 30, tzinfo=pytz.UTC)
    end_date = datetime(2018, 1, 1, 15, 15, tzinfo=pytz.UTC)
    type = ['Testtype1', 'Testtype2']
    address = "Teststreet 1"
    organization_uuid = uuid.uuid4()
    notes = Iterator(['Lorem', 'Ipsum'])


class AppointmentNotification(DjangoModelFactory):
    class Meta:
        model = AppointmentNotificationM

    subject = 'Test Subject'
    message = 'Test Message body'
    recipient = 'test@example.org'
    appointment = SubFactory(Appointment)
