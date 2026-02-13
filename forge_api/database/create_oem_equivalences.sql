-- Script para crear la tabla oem.equivalences
-- Ejecutar en PostgreSQL

-- Verificar si el schema oem existe, si no, crearlo
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'oem') THEN
        CREATE SCHEMA oem;
    END IF;
END $$;

-- Crear la tabla oem.equivalences
CREATE TABLE IF NOT EXISTS oem.equivalences (
    equivalence_id SERIAL PRIMARY KEY,
    oem_part_number VARCHAR(30) NOT NULL,
    oem_code VARCHAR(10) NOT NULL REFERENCES oem_brands(oem_code) ON DELETE CASCADE,
    aftermarket_sku VARCHAR(20),
    equivalence_type VARCHAR(20),
    confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100),
    notes TEXT,
    verified_by INTEGER REFERENCES app.technicians(technician_id) ON DELETE SET NULL,
    verified_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_oem_equivalence UNIQUE (oem_part_number, oem_code, aftermarket_sku)
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_oem_equivalences_oem_code ON oem.equivalences(oem_code);
CREATE INDEX IF NOT EXISTS idx_oem_equivalences_oem_part ON oem.equivalences(oem_part_number);
CREATE INDEX IF NOT EXISTS idx_oem_equivalences_aftermarket ON oem.equivalences(aftermarket_sku);

-- Crear la secuencia si no existe
CREATE SEQUENCE IF NOT EXISTS oem.equivalences_equivalence_id_seq
    AS INTEGER
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

-- Asignar la secuencia a la columna equivalence_id
ALTER TABLE oem.equivalences ALTER COLUMN equivalence_id SET DEFAULT nextval('oem.equivalences_equivalence_id_seq'::regclass);

-- Comentarios
COMMENT ON TABLE oem.equivalences IS 'Tabla de equivalencias entre partes OEM y alternativas del mercado';
COMMENT ON COLUMN oem.equivalences.equivalence_id IS 'Identificador único de la equivalencia';
COMMENT ON COLUMN oem.equivalences.oem_part_number IS 'Número de parte del fabricante original';
COMMENT ON COLUMN oem.equivalences.oem_code IS 'Código de la marca OEM';
COMMENT ON COLUMN oem.equivalences.aftermarket_sku IS 'SKU del producto alternativo del mercado';
COMMENT ON COLUMN oem.equivalences.equivalence_type IS 'Tipo de equivalencia: DIRECT, COMPATIBLE, UPGRADE, DOWNGRADE';
COMMENT ON COLUMN oem.equivalences.confidence_score IS 'Porcentaje de confianza de la equivalencia (0-100)';
COMMENT ON COLUMN oem.equivalences.notes IS 'Notas adicionales sobre la equivalencia';
