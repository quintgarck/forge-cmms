# Crea tabla oem.brand_types (catálogo de tipos de marca en esquema oem)

from django.db import migrations


def move_to_oem_schema(apps, schema_editor):
    """Crea tabla oem.brand_types, copia datos desde public si existe, o inserta por defecto."""
    with schema_editor.connection.cursor() as cursor:
        # Crear tabla en esquema oem con nombre brand_types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oem.brand_types (
                code VARCHAR(20) PRIMARY KEY,
                name_es VARCHAR(80) NOT NULL,
                name_en VARCHAR(80),
                display_order INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Copiar desde public si existe (migración 0013 pudo crear oem_brand_types ahí)
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'oem_brand_types'
            );
        """)
        if cursor.fetchone()[0]:
            cursor.execute("""
                INSERT INTO oem.brand_types (code, name_es, name_en, display_order, is_active, created_at, updated_at)
                SELECT code, name_es, name_en, display_order, is_active, created_at, updated_at
                FROM public.oem_brand_types
                ON CONFLICT (code) DO NOTHING;
            """)
        # Si oem.brand_types sigue vacía, insertar valores por defecto
        cursor.execute("SELECT COUNT(*) FROM oem.brand_types;")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO oem.brand_types (code, name_es, name_en, display_order, is_active)
                VALUES
                    ('VEHICLE_MFG', 'Fabricante de Vehículos', 'Vehicle Manufacturer', 10, TRUE),
                    ('EQUIPMENT_MFG', 'Fabricante de Maquinaria', 'Equipment Manufacturer', 20, TRUE),
                    ('PARTS_SUPPLIER', 'Proveedor de Partes', 'Parts Supplier', 30, TRUE),
                    ('MIXED', 'Mixto', 'Mixed (Manufacturer & Supplier)', 40, TRUE);
            """)
        # Eliminar tabla de public si existe
        cursor.execute("DROP TABLE IF EXISTS public.oem_brand_types CASCADE;")


def reverse_move(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_brand_type_catalog'),
    ]

    operations = [
        migrations.RunPython(move_to_oem_schema, reverse_move),
    ]
