from django.db import migrations, models
import shortuuid
from django.db.models import Count

def final_short_id_fix(apps, schema_editor):
    SpinEntry = apps.get_model('spinwheelapp', 'SpinEntry')
    
    # 1. First ensure all entries have a short_id
    for entry in SpinEntry.objects.filter(short_id__isnull=True):
        entry.short_id = shortuuid.ShortUUID().random(length=8)
        entry.save()
    
    # 2. Fix any duplicates (shouldn't exist but just in case)
    duplicates = SpinEntry.objects.values('short_id').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    for dup in duplicates:
        entries = SpinEntry.objects.filter(short_id=dup['short_id']).order_by('id')
        # Keep first entry, regenerate others
        for entry in entries[1:]:
            new_id = shortuuid.ShortUUID().random(length=8)
            while SpinEntry.objects.filter(short_id=new_id).exists():
                new_id = shortuuid.ShortUUID().random(length=8)
            entry.short_id = new_id
            entry.save()

class Migration(migrations.Migration):
    dependencies = [
        ('spinwheelapp', '0017_alter_spinentry_short_id'),
    ]

    operations = [
        # 1. Temporarily make short_id non-unique
        migrations.AlterField(
            model_name='spinentry',
            name='short_id',
            field=models.CharField(max_length=8, unique=False),
        ),
        
        # 2. Fix the data
        migrations.RunPython(final_short_id_fix),
        
        # 3. Re-enable uniqueness
        migrations.AlterField(
            model_name='spinentry',
            name='short_id',
            field=models.CharField(max_length=8, unique=True),
        ),
    ]