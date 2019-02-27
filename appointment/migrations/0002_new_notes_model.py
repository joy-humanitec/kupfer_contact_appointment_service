import django.contrib.postgres.fields
from django.db import migrations, models

appointment_notes = []


def forwards_before_notes_field_delete(apps, schema_editor):
    """ Save notes to appointment_notes. """
    Appointment = apps.get_model('appointment', 'Appointment')
    db_alias = schema_editor.connection.alias
    for appointment in Appointment.objects.using(db_alias).all():
        if appointment.notes:
            appointment_notes.append({
                'appointment_id': appointment.id,
                'note': appointment.notes
            })


def forwards_after_new_notes_manytomany_creation(apps, schema_editor):
    """ Save notes from appointment_notes to new notes-model. """
    Appointment = apps.get_model('appointment', 'Appointment')
    AppointmentNote = apps.get_model('appointment', 'AppointmentNote')
    db_alias = schema_editor.connection.alias
    for appointment_note in appointment_notes:
        new_note = AppointmentNote.objects.using(db_alias).create(note=appointment_note[
            'note'])
        appointment = Appointment.objects.using(db_alias).get(id=appointment_note[
            'appointment_id'])
        appointment.notes.add(new_note)


def reverse_before_notes_field_delete(apps, schema_editor):
    raise NotImplementedError("Secondary Notes would be lost. "
                              "Sorry, there is no way back.")


def reverse_after_new_notes_manytomany_creation(apps, schema_editor):
    raise NotImplementedError("Secondary Notes would be lost. "
                              "Sorry, there is no way back.")


class Migration(migrations.Migration):

    dependencies = [
        ('appointment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppointmentNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField()),
                ('type', models.IntegerField(choices=[(1, 'Primary'), (2, 'Secondary')], default=1, help_text='Choices: 1, 2')),
            ],
        ),
        migrations.AlterField(
            model_name='appointment',
            name='invitee_uuids',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(), blank=True, help_text='List of CoreUser UUIDs invited to the appointment.', null=True, size=None),
        ),
        migrations.RunPython(forwards_before_notes_field_delete,
                             reverse_before_notes_field_delete),
        migrations.RemoveField(
            model_name='appointment',
            name='notes',
        ),
        migrations.AddField(
            model_name='appointment',
            name='notes',
            field=models.ManyToManyField(to='appointment.AppointmentNote'),
        ),
        migrations.RunPython(forwards_after_new_notes_manytomany_creation,
                             reverse_after_new_notes_manytomany_creation),
    ]
