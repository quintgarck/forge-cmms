-- Script para poblar datos de prueba en el esquema OEM
-- Fecha: 2026-01-10
-- Propósito: Probar integración OEM + Equipos

-- ========================================
-- LIMPIAR DATOS EXISTENTES (opcional)
-- ========================================
-- DELETE FROM oem.equivalences WHERE oem_code IN ('TOYOTA', 'FORD', 'CAT', 'CHEV', 'HONDA');
-- DELETE FROM oem.catalog_items WHERE oem_code IN ('TOYOTA', 'FORD', 'CAT', 'CHEV', 'HONDA');
-- DELETE FROM oem.brands WHERE oem_code IN ('TOYOTA', 'FORD', 'CAT', 'CHEV', 'HONDA');

-- ========================================
-- INSERTAR MARCAS (BRANDS)
-- ========================================

-- Marcas de Vehículos
INSERT INTO oem.brands (oem_code, name, brand_type, country, website, is_active, display_order) VALUES
('TOYOTA', 'Toyota Motor Corporation', 'VEHICLE_MFG', 'JP', 'https://www.toyota.com', true, 1),
('FORD', 'Ford Motor Company', 'VEHICLE_MFG', 'US', 'https://www.ford.com', true, 2),
('CHEV', 'Chevrolet', 'VEHICLE_MFG', 'US', 'https://www.chevrolet.com', true, 3),
('HONDA', 'Honda Motor Co., Ltd.', 'VEHICLE_MFG', 'JP', 'https://www.honda.com', true, 4),
('CAT', 'Caterpillar Inc.', 'EQUIPMENT_MFG', 'US', 'https://www.caterpillar.com', true, 10)
ON CONFLICT (oem_code) DO UPDATE SET
    name = EXCLUDED.name,
    brand_type = EXCLUDED.brand_type,
    country = EXCLUDED.country,
    website = EXCLUDED.website,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = CURRENT_TIMESTAMP;

-- ========================================
-- INSERTAR MODELOS DE VEHÍCULOS (CATALOG_ITEMS)
-- ========================================

-- Modelos Toyota
INSERT INTO oem.catalog_items (
    oem_code, part_number, description_es, description_en, 
    item_type, body_style, year_start, year_end, is_active, display_order
) VALUES
('TOYOTA', 'COROLLA', 'Toyota Corolla', 'Toyota Corolla', 'VEHICLE_MODEL', 'Sedan', 1966, 2024, true, 1),
('TOYOTA', 'CAMRY', 'Toyota Camry', 'Toyota Camry', 'VEHICLE_MODEL', 'Sedan', 1982, 2024, true, 2),
('TOYOTA', 'RAV4', 'Toyota RAV4', 'Toyota RAV4', 'VEHICLE_MODEL', 'SUV', 1994, 2024, true, 3),
('TOYOTA', 'HILUX', 'Toyota Hilux', 'Toyota Hilux', 'VEHICLE_MODEL', 'Pickup', 1968, 2024, true, 4),
('TOYOTA', 'PRIUS', 'Toyota Prius', 'Toyota Prius', 'VEHICLE_MODEL', 'Hybrid', 1997, 2024, true, 5)
ON CONFLICT (oem_code, part_number) DO UPDATE SET
    description_es = EXCLUDED.description_es,
    description_en = EXCLUDED.description_en,
    item_type = EXCLUDED.item_type,
    body_style = EXCLUDED.body_style,
    year_start = EXCLUDED.year_start,
    year_end = EXCLUDED.year_end,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

-- Modelos Ford
INSERT INTO oem.catalog_items (
    oem_code, part_number, description_es, description_en, 
    item_type, body_style, year_start, year_end, is_active, display_order
) VALUES
('FORD', 'F150', 'Ford F-150', 'Ford F-150', 'VEHICLE_MODEL', 'Pickup', 1948, 2024, true, 1),
('FORD', 'MUSTANG', 'Ford Mustang', 'Ford Mustang', 'VEHICLE_MODEL', 'Coupe', 1964, 2024, true, 2),
('FORD', 'EXPLORER', 'Ford Explorer', 'Ford Explorer', 'VEHICLE_MODEL', 'SUV', 1990, 2024, true, 3),
('FORD', 'RANGER', 'Ford Ranger', 'Ford Ranger', 'VEHICLE_MODEL', 'Pickup', 1983, 2024, true, 4),
('FORD', 'ESCAPE', 'Ford Escape', 'Ford Escape', 'VEHICLE_MODEL', 'SUV', 2000, 2024, true, 5)
ON CONFLICT (oem_code, part_number) DO UPDATE SET
    description_es = EXCLUDED.description_es,
    description_en = EXCLUDED.description_en,
    item_type = EXCLUDED.item_type,
    body_style = EXCLUDED.body_style,
    year_start = EXCLUDED.year_start,
    year_end = EXCLUDED.year_end,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

-- Modelos Chevrolet
INSERT INTO oem.catalog_items (
    oem_code, part_number, description_es, description_en, 
    item_type, body_style, year_start, year_end, is_active, display_order
) VALUES
('CHEV', 'SILVERADO', 'Chevrolet Silverado', 'Chevrolet Silverado', 'VEHICLE_MODEL', 'Pickup', 1999, 2024, true, 1),
('CHEV', 'CAMARO', 'Chevrolet Camaro', 'Chevrolet Camaro', 'VEHICLE_MODEL', 'Coupe', 1966, 2024, true, 2),
('CHEV', 'EQUINOX', 'Chevrolet Equinox', 'Chevrolet Equinox', 'VEHICLE_MODEL', 'SUV', 2004, 2024, true, 3),
('CHEV', 'TAHOE', 'Chevrolet Tahoe', 'Chevrolet Tahoe', 'VEHICLE_MODEL', 'SUV', 1992, 2024, true, 4),
('CHEV', 'CORVETTE', 'Chevrolet Corvette', 'Chevrolet Corvette', 'VEHICLE_MODEL', 'Deportivo', 1953, 2024, true, 5)
ON CONFLICT (oem_code, part_number) DO UPDATE SET
    description_es = EXCLUDED.description_es,
    description_en = EXCLUDED.description_en,
    item_type = EXCLUDED.item_type,
    body_style = EXCLUDED.body_style,
    year_start = EXCLUDED.year_start,
    year_end = EXCLUDED.year_end,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

-- Modelos Honda
INSERT INTO oem.catalog_items (
    oem_code, part_number, description_es, description_en, 
    item_type, body_style, year_start, year_end, is_active, display_order
) VALUES
('HONDA', 'CIVIC', 'Honda Civic', 'Honda Civic', 'VEHICLE_MODEL', 'Sedan', 1972, 2024, true, 1),
('HONDA', 'ACCORD', 'Honda Accord', 'Honda Accord', 'VEHICLE_MODEL', 'Sedan', 1976, 2024, true, 2),
('HONDA', 'CRV', 'Honda CR-V', 'Honda CR-V', 'VEHICLE_MODEL', 'SUV', 1995, 2024, true, 3),
('HONDA', 'PILOT', 'Honda Pilot', 'Honda Pilot', 'VEHICLE_MODEL', 'SUV', 2002, 2024, true, 4),
('HONDA', 'FIT', 'Honda Fit', 'Honda Fit', 'VEHICLE_MODEL', 'Hatchback', 2001, 2024, true, 5)
ON CONFLICT (oem_code, part_number) DO UPDATE SET
    description_es = EXCLUDED.description_es,
    description_en = EXCLUDED.description_en,
    item_type = EXCLUDED.item_type,
    body_style = EXCLUDED.body_style,
    year_start = EXCLUDED.year_start,
    year_end = EXCLUDED.year_end,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

-- Modelos de Maquinaria Caterpillar
INSERT INTO oem.catalog_items (
    oem_code, part_number, description_es, description_en, 
    item_type, body_style, year_start, year_end, is_active, display_order
) VALUES
('CAT', '320D', 'Excavadora 320D', 'Excavator 320D', 'EQUIPMENT_MODEL', 'Excavadora', 2000, 2024, true, 1),
('CAT', '950M', 'Cargador de Ruedas 950M', 'Wheel Loader 950M', 'EQUIPMENT_MODEL', 'Cargador', 2012, 2024, true, 2),
('CAT', 'D6T', 'Tractor D6T', 'Dozer D6T', 'EQUIPMENT_MODEL', 'Tractor', 2008, 2024, true, 3),
('CAT', '730C', 'Camión Articulado 730C', 'Articulated Truck 730C', 'EQUIPMENT_MODEL', 'Camión', 2008, 2024, true, 4),
('CAT', '140M', 'Motoniveladora 140M', 'Motor Grader 140M', 'EQUIPMENT_MODEL', 'Motoniveladora', 2008, 2024, true, 5)
ON CONFLICT (oem_code, part_number) DO UPDATE SET
    description_es = EXCLUDED.description_es,
    description_en = EXCLUDED.description_en,
    item_type = EXCLUDED.item_type,
    body_style = EXCLUDED.body_style,
    year_start = EXCLUDED.year_start,
    year_end = EXCLUDED.year_end,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = now();

-- ========================================
-- VERIFICACIÓN
-- ========================================

-- Contar marcas insertadas
SELECT 'MARCAS INSERTADAS:' as mensaje, COUNT(*) as total 
FROM oem.brands 
WHERE oem_code IN ('TOYOTA', 'FORD', 'CAT', 'CHEV', 'HONDA');

-- Contar modelos insertados
SELECT 'MODELOS INSERTADOS:' as mensaje, COUNT(*) as total 
FROM oem.catalog_items 
WHERE oem_code IN ('TOYOTA', 'FORD', 'CAT', 'CHEV', 'HONDA')
  AND item_type IN ('VEHICLE_MODEL', 'EQUIPMENT_MODEL');

-- Listar marcas
SELECT oem_code, name, brand_type, is_active 
FROM oem.brands 
WHERE oem_code IN ('TOYOTA', 'FORD', 'CAT', 'CHEV', 'HONDA')
ORDER BY display_order;

-- Listar modelos por marca
SELECT b.oem_code, b.name, ci.part_number, ci.description_es, ci.body_style, ci.year_start, ci.year_end
FROM oem.catalog_items ci
JOIN oem.brands b ON ci.oem_code = b.oem_code
WHERE ci.oem_code IN ('TOYOTA', 'FORD', 'CAT', 'CHEV', 'HONDA')
  AND ci.item_type IN ('VEHICLE_MODEL', 'EQUIPMENT_MODEL')
ORDER BY b.display_order, ci.display_order;
