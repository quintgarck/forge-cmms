# Tablas cat.product_category y cat.product_type para categoría y tipo de producto (inventario).

from django.db import migrations


def create_tables_and_seed(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        # cat.product_category
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cat.product_category (
                code VARCHAR(20) PRIMARY KEY,
                name_es VARCHAR(80) NOT NULL,
                name_en VARCHAR(80),
                display_order INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("SELECT COUNT(*) FROM cat.product_category;")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO cat.product_category (code, name_es, name_en, display_order, is_active)
                VALUES
                    ('service', 'Servicio', 'Service', 10, TRUE),
                    ('part', 'Parte/Repuesto', 'Part', 20, TRUE),
                    ('material', 'Material', 'Material', 30, TRUE),
                    ('tool', 'Herramienta', 'Tool', 40, TRUE),
                    ('consumable', 'Consumible', 'Consumable', 50, TRUE),
                    ('accessory', 'Accesorio', 'Accessory', 60, TRUE)
                ON CONFLICT (code) DO NOTHING;
            """)
        # cat.product_type
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cat.product_type (
                code VARCHAR(20) PRIMARY KEY,
                name_es VARCHAR(80) NOT NULL,
                name_en VARCHAR(80),
                display_order INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("SELECT COUNT(*) FROM cat.product_type;")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO cat.product_type (code, name_es, name_en, display_order, is_active)
                VALUES
                    ('service', 'Servicio', 'Service', 10, TRUE),
                    ('part', 'Parte', 'Part', 20, TRUE),
                    ('material', 'Material', 'Material', 30, TRUE)
                ON CONFLICT (code) DO NOTHING;
            """)


def reverse_app(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS cat.product_type;")
        cursor.execute("DROP TABLE IF EXISTS cat.product_category;")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_seed_uom_codes'),
    ]

    operations = [
        migrations.RunPython(create_tables_and_seed, reverse_app),
    ]
