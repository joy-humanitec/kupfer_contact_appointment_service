# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import escape
from django.core.mail import send_mail

from datetime import timedelta
from contact.models import Contact

try:
    from django.utils import timezone
except ImportError:
    from datetime import datetime as timezone

logger = logging.getLogger(__name__)


class AppointmentNotificationEMail():
    appointment_notification = None

    def __init__(self, appointment_notification):
        self.appointment_notification = appointment_notification

    def notify_recipient(self):
        if not self.appointment_notification.sent_at:
            html_msg = escape(
                self.appointment_notification.message).replace('\n', '<br>')
            html_alt = "<html><head><meta charset=\"UTF-8\"><title></title>" \
                       "</head><body>" + html_msg + "</body></html>"

            send_mail(
                self.appointment_notification.subject,
                self.appointment_notification.message,
                settings.DEFAULT_FROM_EMAIL,
                [self.appointment_notification.recipient],
                fail_silently=False,
                html_message=html_alt
            )

            self.appointment_notification.sent_at = timezone.now()
            logger.info('EMail notification has been send for appointment'
                        '{}'.format(self.appointment_notification.appointment))
        else:
            logger.warn('EMail notification could not been send for '
                        'appointment {} message already sent'
                        ''.format(self.appointment_notification.appointment))

    def generate_message(self):
        appointment = self.appointment_notification.appointment

        date = appointment.start_date.strftime('%d. %B %Y')
        if appointment.end_date - appointment.end_date > \
                timedelta(1):
            date = date + ' - ' + appointment.end_date.strftime(
                '%d. %B %Y')

        appointment_delta = appointment.start_date - timezone.now()

        if appointment.address:
            address = appointment.address
        else:
            contact = Contact.objects.get(uuid=appointment.contact_uuid)
            addresses = contact.format_addresses()

            if 'delivery' in addresses:
                address = addresses['delivery']
            elif 'home' in addresses:
                address = addresses['home']
            elif 'business' in addresses:
                address = addresses['business']
            elif 'billing' in addresses:
                address = addresses['billing']
            elif 'mailing' in addresses:
                address = addresses['mailing']
            else:
                address = None

        context = {
            'appointment_date': date,
            'appointment_start_time':
                appointment.start_date.strftime('%M:%H'),
            'appointment_end_time':
                appointment.end_date.strftime('%M:%H'),
            'project_address': address,
            'organization_phone_number':
                self.appointment_notification.org_phone,
            'organization':
                self.appointment_notification.org_name,
            'timedelta': str(appointment_delta.days),
        }

        rendered_message = render_to_string(
            'appointment_notification_message.txt',
            context)
        rendered_subject = render_to_string(
            'appointment_notification_subject.txt',
            context)

        self.appointment_notification.message = rendered_message
        self.appointment_notification.subject = rendered_subject
        return (rendered_subject, rendered_message)
