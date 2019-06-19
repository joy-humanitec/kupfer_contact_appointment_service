import random
from datetime import datetime
import pytz
import uuid
import factory

from factory import DjangoModelFactory, Iterator, SubFactory, RelatedFactory

from ..models import Appointment as AppointmentM
from ..models import AppointmentNotification as AppointmentNotificationM
from ..models import AppointmentNote as ApppointmentNoteM
from ..models import AppointmentDrivingTime as AppointmentDrivingTimeM


class AppointmentNote(DjangoModelFactory):
    class Meta:
        model = ApppointmentNoteM


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
    notes = RelatedFactory(AppointmentNote)


class AppointmentNotification(DjangoModelFactory):
    class Meta:
        model = AppointmentNotificationM

    subject = 'Test Subject'
    message = 'Test Message body'
    recipient = 'test@example.org'
    appointment = SubFactory(Appointment)


class AppointmentDrivingTime(DjangoModelFactory):
    distance = factory.LazyAttribute(lambda x: float(random.randrange(0, 10000)/100))
    time = factory.LazyAttribute(lambda x: float(random.randrange(0, 120)))

    class Meta:
        model = AppointmentDrivingTimeM

    appointment = SubFactory(Appointment)
