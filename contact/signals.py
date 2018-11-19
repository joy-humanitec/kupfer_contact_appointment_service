from django.dispatch import receiver
from django.db.models.signals import pre_save
from .models import Contact


@receiver(pre_save, sender=Contact)
def pre_save_handler(sender, instance, *args, **kwargs):
    instance.full_clean()
