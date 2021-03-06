# Generated by Django 2.2.1 on 2019-06-24 12:48
from collections import defaultdict

from django.db import migrations, models


def prepare_for_int_conversion(apps, schema_editor):
    Contact = apps.get_model('contact', 'Contact')
    contacts= set()
    max_id_for_org = defaultdict(int)
    failed_items = []

    for contact in Contact.objects.filter(customer_id__isnull=False):
        org_uuid = contact.organization_uuid
        customer_id = int(contact.customer_id)
        if (org_uuid, customer_id) in contacts:
            failed_items.append(contact)
        else:
            contacts.add((org_uuid, customer_id))
            max_id_for_org[org_uuid] = max(max_id_for_org[org_uuid], customer_id)

    # Update items that breaks unique constraint when converting to int with new values
    for contact in failed_items:
        new_val = max_id_for_org[contact.organization_uuid] + 1
        contact.customer_id = str(new_val)
        contact.save()
        max_id_for_org[contact.organization_uuid] = new_val


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0017_migrate_contact_type'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='contact',
            name='unique_organization_customer_id',
        ),
        migrations.RunPython(prepare_for_int_conversion, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='contact',
            name='customer_id',
            field=models.IntegerField(blank=True, help_text='ID set by the customer. Must be unique in organization.', null=True),
        ),
        migrations.AddConstraint(
            model_name='contact',
            constraint=models.UniqueConstraint(condition=models.Q(_negated=True, customer_id=None),
                                               fields=('organization_uuid', 'customer_id'),
                                               name='unique_organization_customer_id'),
        ),
    ]
