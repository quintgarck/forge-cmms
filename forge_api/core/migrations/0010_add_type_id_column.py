# Generated migration to add type_id column to equipment table
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_allow_null_type_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipment',
            name='type_id',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
    ]
