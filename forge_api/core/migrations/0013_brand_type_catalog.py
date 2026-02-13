# Catálogo de tipos de marca (escalable, gestionable desde BD)

from django.db import migrations, models


def seed_brand_types(apps, schema_editor):
    BrandType = apps.get_model('core', 'BrandType')
    if BrandType.objects.exists():
        return
    BrandType.objects.bulk_create([
        BrandType(code='VEHICLE_MFG', name_es='Fabricante de Vehículos', name_en='Vehicle Manufacturer', display_order=10),
        BrandType(code='EQUIPMENT_MFG', name_es='Fabricante de Maquinaria', name_en='Equipment Manufacturer', display_order=20),
        BrandType(code='PARTS_SUPPLIER', name_es='Proveedor de Partes', name_en='Parts Supplier', display_order=30),
        BrandType(code='MIXED', name_es='Mixto', name_en='Mixed (Manufacturer & Supplier)', display_order=40),
    ])


def reverse_seed(apps, schema_editor):
    apps.get_model('core', 'BrandType').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_add_oem_brands_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrandType',
            fields=[
                ('code', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('name_es', models.CharField(max_length=80)),
                ('name_en', models.CharField(blank=True, max_length=80, null=True)),
                ('display_order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'oem_brand_types',
                'ordering': ['display_order', 'code'],
                'verbose_name': 'Tipo de marca',
                'verbose_name_plural': 'Tipos de marca',
            },
        ),
        migrations.RunPython(seed_brand_types, reverse_seed),
    ]
