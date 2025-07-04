# Generated by Django 5.2.3 on 2025-07-05 06:57

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spinwheelapp', '0007_shopprofile_whatsapp_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopsettings',
            name='game_type',
            field=models.CharField(choices=[('SW', 'Spin Wheel'), ('SC', 'Scratch Card')], default='SW', max_length=2),
        ),
        migrations.AlterField(
            model_name='shopprofile',
            name='whatsapp_number',
            field=models.CharField(default='918848647616', help_text='WhatsApp number with country code (e.g. 919876543210)', max_length=15, validators=[django.core.validators.RegexValidator('^[0-9]+$', 'Enter a valid phone number')]),
        ),
    ]
