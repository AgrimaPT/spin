from django.db import migrations, models

def clean_duplicates(apps, schema_editor):
    SpinEntry = apps.get_model('spinwheelapp', 'SpinEntry')
    from django.db.models import Count
    
    duplicates = (
        SpinEntry.objects.values('shop', 'bill_number')
        .annotate(count=Count('id'))
        .filter(count__gt=1, bill_number__isnull=False)
    )
    
    for dup in duplicates:
        entries = SpinEntry.objects.filter(
            shop_id=dup['shop'],
            bill_number=dup['bill_number']
        ).order_by('-timestamp')  # Keep most recent
        
        for entry in entries[1:]:  # Nullify older duplicates
            entry.bill_number = None
            entry.save()

class Migration(migrations.Migration):
    dependencies = [
        ('spinwheelapp', '0008_shopsettings_game_type_and_more'),
    ]

    operations = [
        migrations.RunPython(clean_duplicates),  # Clean FIRST
        migrations.AddConstraint(  # Then add constraint
            model_name='spinentry',
            constraint=models.UniqueConstraint(
                condition=models.Q(('bill_number__isnull', False)),
                fields=('shop', 'bill_number'),
                name='unique_bill_per_shop'
            ),
        ),
    ]