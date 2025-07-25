from django.db import migrations, models
import shortuuid
from django.db.models import Count

def finalize_short_ids(apps, schema_editor):
    SpinEntry = apps.get_model('spinwheelapp', 'SpinEntry')
    
    # 1. Ensure no null values exist
    null_entries = SpinEntry.objects.filter(short_id__isnull=True)
    for entry in null_entries:
        entry.short_id = shortuuid.ShortUUID().random(length=8)
        entry.save()
    
    # 2. Find and fix any duplicates
    duplicates = SpinEntry.objects.values('short_id').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    for dup in duplicates:
        # Get all entries with this duplicate ID (keep oldest)
        entries = SpinEntry.objects.filter(
            short_id=dup['short_id']
        ).order_by('id')
        
        # Regenerate IDs for duplicates (skip first one)
        for entry in entries[1:]:
            new_id = shortuuid.ShortUUID().random(length=8)
            while SpinEntry.objects.filter(short_id=new_id).exists():
                new_id = shortuuid.ShortUUID().random(length=8)
            entry.short_id = new_id
            entry.save()

class Migration(migrations.Migration):
    dependencies = [
        ('spinwheelapp', '0015_alter_spinentry_short_id'),
    ]

    operations = [
        # 1. Temporarily remove constraints
        migrations.AlterField(
            model_name='spinentry',
            name='short_id',
            field=models.CharField(max_length=8, null=True, unique=False),
        ),
        
        # 2. Clean the data
        migrations.RunPython(finalize_short_ids),
        
        # 3. Reapply constraints
        migrations.AlterField(
            model_name='spinentry',
            name='short_id',
            field=models.CharField(max_length=8, unique=True),
        ),
    ]