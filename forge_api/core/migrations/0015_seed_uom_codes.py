# Inserta unidades de medida por defecto en cat.uom_codes si la tabla está vacía.

from django.db import migrations


def seed_uom_codes(apps, schema_editor):
    """Inserta registros por defecto en cat.uom_codes si no hay ninguno."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM cat.uom_codes;")
        if cursor.fetchone()[0] > 0:
            return
        cursor.execute("""
            INSERT INTO cat.uom_codes (uom_code, name_es, name_en, is_fractional)
            VALUES
                ('EA', 'Unidad', 'Each', FALSE),
                ('HR', 'Hora', 'Hour', FALSE),
                ('KG', 'Kilogramo', 'Kilogram', FALSE),
                ('L', 'Litro', 'Liter', FALSE),
                ('M', 'Metro', 'Meter', FALSE),
                ('BX', 'Caja', 'Box', FALSE),
                ('PK', 'Paquete', 'Pack', FALSE),
                ('SET', 'Juego', 'Set', FALSE)
            ON CONFLICT (uom_code) DO NOTHING;
        """)


def reverse_seed(apps, schema_editor):
    """Opcional: no borramos datos para no perder personalizaciones."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_move_brand_types_to_oem_schema'),
    ]

    operations = [
        migrations.RunPython(seed_uom_codes, reverse_seed),
    ]
