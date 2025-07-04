# Generated by Django 5.2.3 on 2025-07-04 06:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spinwheelapp', '0002_remove_spinentry_unique_bill_per_shop_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='spinentry',
            constraint=models.UniqueConstraint(condition=models.Q(('bill_number__isnull', False)), fields=('shop', 'bill_number'), name='unique_bill_per_shop'),
        ),
    ]
