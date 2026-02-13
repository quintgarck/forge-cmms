-- SQL para crear la tabla oem.catalog_items en PostgreSQL
-- Ejecutar este script en la base de datos ForgeDB

-- Verificar si el esquema oem existe, si no crearlo
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'oem') THEN
        CREATE SCHEMA oem;
        RAISE NOTICE 'Esquema oem creado';
    ELSE
        RAISE NOTICE 'Esquema oem ya existe';
    END IF;
END $$;

-- Crear la tabla oem.catalog_items
CREATE TABLE IF NOT EXISTS oem.catalog_items (
    catalog_id SERIAL PRIMARY KEY,
    oem_code VARCHAR(10) NOT NULL REFERENCES core.oem_brands(oem_code),
    item_type VARCHAR(20) DEFAULT 'PART' NOT NULL,
    part_number VARCHAR(30) NOT NULL,
    part_number_type VARCHAR(15),
    description_es TEXT,
    description_en TEXT,
    group_code VARCHAR(20) REFERENCES core.taxonomy_groups(group_code),
    body_style VARCHAR(50),
    year_start SMALLINT,
    year_end SMALLINT,
    weight_kg DECIMAL(8,3),
    dimensions VARCHAR(100),
    material VARCHAR(50),
    primary_image_url VARCHAR(500),
    vin_patterns JSONB DEFAULT '[]'::jsonb,
    model_codes JSONB DEFAULT '[]'::jsonb,
    body_codes JSONB DEFAULT '[]'::jsonb,
    engine_codes JSONB DEFAULT '[]'::jsonb,
    transmission_codes JSONB DEFAULT '[]'::jsonb,
    axle_codes JSONB DEFAULT '[]'::jsonb,
    color_codes JSONB DEFAULT '[]'::jsonb,
    trim_codes JSONB DEFAULT '[]'::jsonb,
    manual_types JSONB DEFAULT '[]'::jsonb,
    manual_refs JSONB DEFAULT '[]'::jsonb,
    list_price DECIMAL(10,2),
    net_price DECIMAL(10,2),
    currency_code VARCHAR(3) DEFAULT 'USD',
    oem_lead_time_days INTEGER,
    is_discontinued BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    valid_from DATE,
    valid_until DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índice único en oem_code + part_number
CREATE UNIQUE INDEX IF NOT EXISTS oem_catalog_items_oem_part_unique 
ON oem.catalog_items(oem_code, part_number);

-- Crear índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS oem_catalog_items_oem_code_idx 
ON oem.catalog_items(oem_code);

CREATE INDEX IF NOT EXISTS oem_catalog_items_part_number_idx 
ON oem.catalog_items(part_number);

CREATE INDEX IF NOT EXISTS oem_catalog_items_item_type_idx 
ON oem.catalog_items(item_type);

CREATE INDEX IF NOT EXISTS oem_catalog_items_is_active_idx 
ON oem.catalog_items(is_active);

CREATE INDEX IF NOT EXISTS oem_catalog_items_group_code_idx 
ON oem.catalog_items(group_code);

-- Agregar comentario a la tabla
COMMENT ON TABLE oem.catalog_items IS 'Catálogo de items OEM (vehículos, equipos, partes)';

-- Verificar que se creó correctamente
DO $$
BEGIN
    RAISE NOTICE 'Tabla oem.catalog_items creada/verificada exitosamente';
END $$;
