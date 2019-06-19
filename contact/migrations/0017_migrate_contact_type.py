import uuid

from django.db import migrations, models
import django.db.models.deletion

CONTACT_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('supplier', 'Supplier'),
    ('producer', 'Producer'),
    ('personnel', 'Personnel'),
)


def contact_type_choices_to_contact_type_model(apps, schema_editor):
    """Get the type-choices from all contacts and save it in the type-FK-field."""
    Contact = apps.get_model('contact', 'Contact')
    Type = apps.get_model('contact', 'Type')
    db_alias = schema_editor.connection.alias
    organization_uuid = uuid.uuid4()
    for contact in Contact.objects.using(db_alias).all():
        if contact.contact_type_old:
            contact_type, created = Type.objects.get_or_create(
                is_global=True,
                name=contact.get_contact_type_old_display(),
                defaults={'organization_uuid': organization_uuid}
            )
            contact.contact_type = contact_type
            contact.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0016_type'),
    ]

    operations = [

        migrations.RenameField(
            model_name='contact',
            old_name='contact_type',
            new_name='contact_type_old',
        ),

        migrations.AddField(
            model_name='contact',
            name='contact_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='contact.Type'),
        ),

        migrations.RunPython(contact_type_choices_to_contact_type_model, migrations.RunPython.noop),

        migrations.RemoveField(
            model_name='contact',
            name='contact_type_old',
        ),

    ]
