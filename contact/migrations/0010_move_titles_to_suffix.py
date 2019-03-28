import uuid

from django.db import migrations, models


def move_titles_to_suffix(apps, schema_editor):
    """Normalize titles for swagger compliancy and fill suffixes."""
    Contact = apps.get_model('contact', 'Contact')
    db_alias = schema_editor.connection.alias
    title_choices = ('mr', 'ms', 'mrs', 'miss', 'family')
    for contact in Contact.objects.using(db_alias).all():
        if contact.title not in title_choices:
            suffix = getattr(contact, 'title') or ''
            contact.suffix = suffix
            contact.title = None
            for title_choice in title_choices:
                if title_choice in suffix.lower():
                    contact.title = title_choice
                    contact.suffix = ''
            if 'frau' in suffix.lower():
                contact.title = 'mrs'
                contact.suffix = ''
            if 'herr' in suffix.lower():
                contact.title = 'mr'
                contact.suffix = ''
            if 'familie' in suffix.lower():
                contact.title = 'family'
                contact.suffix = ''
            contact.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0009_auto_20190327_0910'),
    ]

    operations = [
        migrations.RunPython(move_titles_to_suffix, migrations.RunPython.noop),
    ]
