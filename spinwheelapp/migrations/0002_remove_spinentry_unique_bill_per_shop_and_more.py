# Generated by Django 5.2.3 on 2025-07-03 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spinwheelapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='spinentry',
            name='unique_bill_per_shop',
        ),
        migrations.AlterField(
            model_name='shopprofile',
            name='shop_code',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]
