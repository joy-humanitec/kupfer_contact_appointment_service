from django.dispatch import receiver
from django.db.models.signals import pre_save
from .models import Appointment, AppointmentNotification
from .notifications import AppointmentNotificationEMail


@receiver(pre_save, sender=Appointment)
def pre_save_handler(sender, instance, *args, **kwargs):
    instance.full_clean()


@receiver(pre_save, sender=AppointmentNotification)
def pre_save_handler_appointment_notification(sender, instance, *args,
                                              **kwargs):
    instance.full_clean()

    ap_mail = AppointmentNotificationEMail(instance)

    if not instance.message:
        ap_mail.generate_message()

    if instance.send_notification and not instance.sent_at:
        ap_mail.notify_recipient()
