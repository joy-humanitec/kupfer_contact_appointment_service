# Generated by Django 2.0.9 on 2019-03-18 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0007_auto_20190318_1119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='middle_name',
            field=models.CharField(blank=True, default='', help_text='Middle name (not common in Germany)', max_length=50),
            preserve_default=False,
        ),
    ]
