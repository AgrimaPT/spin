from django.db import migrations, models
import shortuuid
from django.db.models import Count

def populate_short_ids(apps, schema_editor):
    SpinEntry = apps.get_model('spinwheelapp', 'SpinEntry')
    
    # First pass: populate all null short_ids
    for entry in SpinEntry.objects.filter(short_id__isnull=True):
        entry.short_id = shortuuid.ShortUUID().random(length=8)
        entry.save()
    
    # Second pass: ensure no duplicates exist
    duplicate_groups = SpinEntry.objects.values('short_id').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    for group in duplicate_groups:
        # Get all entries with this duplicate short_id
        entries = SpinEntry.objects.filter(
            short_id=group['short_id']
        ).order_by('id')
        
        # Keep first entry's ID, regenerate others
        for entry in entries[1:]:
            while True:
                new_id = shortuuid.ShortUUID().random(length=8)
                if not SpinEntry.objects.filter(short_id=new_id).exists():
                    entry.short_id = new_id
                    entry.save()
                    break

class Migration(migrations.Migration):
    dependencies = [
        ('spinwheelapp', '0013_alter_spinentry_short_id'),
    ]

    operations = [
        # Temporarily make short_id non-unique and nullable
        migrations.AlterField(
            model_name='spinentry',
            name='short_id',
            field=models.CharField(max_length=8, null=True, blank=True, unique=False),
        ),
        
        # Populate and fix data
        migrations.RunPython(populate_short_ids),
        
        # Re-apply constraints
        migrations.AlterField(
            model_name='spinentry',
            name='short_id',
            field=models.CharField(max_length=8, unique=True),
        ),
    ]