-- =====================================================
-- PARTE 1: ESQUEMA COMPLETO - LO MEJOR DE AMBAS VERSIONES
-- =====================================================

-- 0. CONFIGURACIÓN INICIAL
SET client_encoding = 'UTF8';
SET search_path TO cat, inv, svc, doc, kpi, app, oem, public;

-- Crear database (ejecutar separado si no existe)
-- CREATE DATABASE forge_db WITH ENCODING 'UTF8' TEMPLATE template0;

-- Crear schemas
CREATE SCHEMA IF NOT EXISTS cat;
CREATE SCHEMA IF NOT EXISTS inv;
CREATE SCHEMA IF NOT EXISTS svc;
CREATE SCHEMA IF NOT EXISTS doc;
CREATE SCHEMA IF NOT EXISTS kpi;
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS oem;

-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- =====================================================
-- 1. CATÁLOGOS MAESTROS - MEJORADO CON CHECK CONSTRAINTS
-- =====================================================

-- 1.1 Equipment types
CREATE TABLE cat.equipment_types (
    type_id SERIAL PRIMARY KEY,
    type_code VARCHAR(20) UNIQUE NOT NULL,
    category VARCHAR(30) NOT NULL CHECK (category IN ('AUTOMOTRIZ','INDUSTRIAL','AGRÍCOLA','CONSTRUCCIÓN','ELECTRÓNICO','OTRO')),
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(50),
    color VARCHAR(20),
    attr_schema JSONB DEFAULT '{}',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 1.2 Equipment - CON TODAS LAS MEJORAS
CREATE TABLE cat.equipment (
    equipment_id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    equipment_code VARCHAR(40) UNIQUE NOT NULL,
    type_id INT NOT NULL REFERENCES cat.equipment_types(type_id) ON DELETE RESTRICT,
    brand VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year SMALLINT CHECK (year >= 1900),
    serial_number VARCHAR(100),
    vin VARCHAR(17),
    license_plate VARCHAR(20),
    color VARCHAR(30),
    submodel_trim VARCHAR(40),
    body_style VARCHAR(20),
    doors SMALLINT,
    engine_desc VARCHAR(100),
    fuel_code VARCHAR(10) REFERENCES cat.fuel_codes(fuel_code),
    aspiration_code VARCHAR(10) REFERENCES cat.aspiration_codes(aspiration_code),
    transmission_code VARCHAR(10) REFERENCES cat.transmission_codes(transmission_code),
    drivetrain_code VARCHAR(10) REFERENCES cat.drivetrain_codes(drivetrain_code),
    client_id INT REFERENCES cat.clients(client_id) ON DELETE SET NULL,
    purchase_date DATE,
    warranty_until DATE,
    last_service_date DATE,
    next_service_date DATE,
    total_service_hours INTEGER DEFAULT 0 CHECK (total_service_hours >= 0),
    total_service_cost DECIMAL(12,2) DEFAULT 0 CHECK (total_service_cost >= 0),
    status VARCHAR(20) DEFAULT 'ACTIVO' CHECK (status IN ('ACTIVO','INACTIVO','REPARACIÓN','BAJA','GARANTÍA')),
    current_mileage_hours INTEGER DEFAULT 0 CHECK (current_mileage_hours >= 0),
    last_mileage_update DATE,
    custom_fields JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_by INT REFERENCES cat.technicians(technician_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- 1.3 Taxonomía completa
CREATE TABLE cat.taxonomy_systems (
    system_code VARCHAR(10) PRIMARY KEY,
    category VARCHAR(30) DEFAULT 'AUTOMOTRIZ',
    name_es VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    icon VARCHAR(50),
    scope TEXT,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cat.taxonomy_subsystems (
    subsystem_code VARCHAR(20) PRIMARY KEY,
    system_code VARCHAR(10) NOT NULL REFERENCES cat.taxonomy_systems(system_code) ON DELETE CASCADE,
    name_es VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    icon VARCHAR(50),
    notes TEXT,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cat.taxonomy_groups (
    group_code VARCHAR(20) PRIMARY KEY,
    subsystem_code VARCHAR(20) NOT NULL REFERENCES cat.taxonomy_subsystems(subsystem_code) ON DELETE CASCADE,
    system_code VARCHAR(10) NOT NULL REFERENCES cat.taxonomy_systems(system_code) ON DELETE CASCADE,
    name_es VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    description TEXT,
    examples TEXT,
    keywords TEXT,
    requires_position BOOLEAN DEFAULT FALSE,
    requires_color BOOLEAN DEFAULT FALSE,
    requires_finish BOOLEAN DEFAULT FALSE,
    requires_side BOOLEAN DEFAULT FALSE,
    typical_position_set TEXT,
    typical_uom VARCHAR(10),
    full_path VARCHAR(200) GENERATED ALWAYS AS (system_code || ' > ' || subsystem_code || ' > ' || name_es) STORED,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 1.4 Códigos auxiliares completos
CREATE TABLE cat.position_codes (
    position_code VARCHAR(15) PRIMARY KEY,
    name_es VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    category VARCHAR(20) CHECK (category IN ('SIDE', 'CORNER', 'ZONE', 'RELATIVE')),
    sort_order INT DEFAULT 0,
    synonyms TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cat.finish_codes (
    finish_code VARCHAR(10) PRIMARY KEY,
    name_es VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    requires_color BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cat.color_codes (
    color_id SERIAL PRIMARY KEY,
    color_code VARCHAR(10) NOT NULL,
    brand VARCHAR(30) DEFAULT 'GENERIC',
    name_es VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    hex_code VARCHAR(7),
    paint_type VARCHAR(20),
    is_metallic BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(brand, color_code)
);

CREATE TABLE cat.source_codes (
    source_code VARCHAR(10) PRIMARY KEY,
    name_es VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    quality_level VARCHAR(10) CHECK (quality_level IN ('LOW', 'MEDIUM', 'HIGH', 'PREMIUM')),
    sort_order INT DEFAULT 0
);

CREATE TABLE cat.condition_codes (
    condition_code VARCHAR(10) PRIMARY KEY,
    name_es VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    requires_core BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0
);

CREATE TABLE cat.uom_codes (
    uom_code VARCHAR(10) PRIMARY KEY,
    name_es VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    is_fractional BOOLEAN DEFAULT FALSE,
    category VARCHAR(20)
);

CREATE TABLE cat.fuel_codes (
    fuel_code VARCHAR(10) PRIMARY KEY,
    name_es VARCHAR(30) NOT NULL,
    name_en VARCHAR(30),
    is_alternative BOOLEAN DEFAULT FALSE
);

CREATE TABLE cat.aspiration_codes (
    aspiration_code VARCHAR(10) PRIMARY KEY,
    name_es VARCHAR(30) NOT NULL,
    name_en VARCHAR(30)
);

CREATE TABLE cat.transmission_codes (
    transmission_code VARCHAR(10) PRIMARY KEY,
    name_es VARCHAR(30) NOT NULL,
    name_en VARCHAR(30)
);

CREATE TABLE cat.drivetrain_codes (
    drivetrain_code VARCHAR(10) PRIMARY KEY,
    name_es VARCHAR(30) NOT NULL,
    name_en VARCHAR(30)
);

CREATE TABLE cat.currencies (
    currency_code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    symbol VARCHAR(5),
    exchange_rate DECIMAL(10,4) DEFAULT 1.0 CHECK (exchange_rate > 0),
    decimals INT DEFAULT 2 CHECK (decimals >= 0),
    is_active BOOLEAN DEFAULT TRUE
);

-- 1.5 Entidades maestras con CHECK constraints mejorados
CREATE TABLE cat.clients (
    client_id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    client_code VARCHAR(20) UNIQUE NOT NULL,
    type VARCHAR(15) NOT NULL CHECK (type IN ('INDIVIDUAL','EMPRESA','GOVERNMENT')),
    name VARCHAR(150) NOT NULL,
    legal_name VARCHAR(150),
    tax_id VARCHAR(30),
    email VARCHAR(100),
    phone VARCHAR(30),
    mobile VARCHAR(30),
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    postal_code VARCHAR(20),
    credit_limit DECIMAL(12,2) DEFAULT 0 CHECK (credit_limit >= 0),
    payment_days INTEGER DEFAULT 30 CHECK (payment_days >= 0),
    credit_used DECIMAL(12,2) DEFAULT 0 CHECK (credit_used >= 0),
    preferred_contact_method VARCHAR(20) DEFAULT 'EMAIL' CHECK (preferred_contact_method IN ('EMAIL','PHONE','SMS','WHATSAPP')),
    send_reminders BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE','BLOCKED')),
    created_by INT REFERENCES cat.technicians(technician_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE cat.technicians (
    technician_id SERIAL PRIMARY KEY,
    employee_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    hire_date DATE,
    birth_date DATE CHECK (birth_date <= CURRENT_DATE),
    specialization VARCHAR(100)[] DEFAULT '{}',
    certification_level VARCHAR(50),
    certifications TEXT[] DEFAULT '{}',
    hourly_rate DECIMAL(10,2) DEFAULT 0 CHECK (hourly_rate >= 0),
    daily_rate DECIMAL(10,2) DEFAULT 0 CHECK (daily_rate >= 0),
    overtime_multiplier DECIMAL(3,2) DEFAULT 1.5 CHECK (overtime_multiplier >= 1.0),
    work_schedule JSONB DEFAULT '{"mon": true, "tue": true, "wed": true, "thu": true, "fri": true}',
    efficiency_avg DECIMAL(5,2) DEFAULT 100.00 CHECK (efficiency_avg BETWEEN 0 AND 200),
    quality_score DECIMAL(5,2) DEFAULT 100.00 CHECK (quality_score BETWEEN 0 AND 100),
    jobs_completed INT DEFAULT 0 CHECK (jobs_completed >= 0),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE','VACATION','SICK')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE cat.suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    contact_email VARCHAR(100),
    contact_phone VARCHAR(20),
    website VARCHAR(200),
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    tax_id VARCHAR(30),
    payment_terms INTEGER DEFAULT 30 CHECK (payment_terms >= 0),
    currency_code VARCHAR(3) DEFAULT 'USD',
    rating DECIMAL(3,2) DEFAULT 5.0 CHECK (rating BETWEEN 0 AND 5.0),
    delivery_time_avg INTEGER DEFAULT 7 CHECK (delivery_time_avg >= 0),
    quality_score DECIMAL(3,2) DEFAULT 5.0 CHECK (quality_score BETWEEN 0 AND 5.0),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    is_preferred BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE cat.fitment (
    fitment_id SERIAL PRIMARY KEY,
    internal_sku VARCHAR(20) REFERENCES inv.product_master(internal_sku) ON DELETE CASCADE,
    equipment_id INT REFERENCES cat.equipment(equipment_id) ON DELETE CASCADE,
    score SMALLINT CHECK (score BETWEEN 0 AND 100) DEFAULT 100,
    notes TEXT,
    verified_by INT REFERENCES cat.technicians(technician_id),
    verified_date DATE CHECK (verified_date <= CURRENT_DATE),
    is_primary_fit BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(internal_sku, equipment_id)
);

-- =====================================================
-- 2. OEM - CON TODAS LAS VALIDACIONES
-- =====================================================
CREATE TABLE oem.brands (
    brand_id SERIAL PRIMARY KEY,
    oem_code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    country VARCHAR(50),
    website VARCHAR(200),
    support_email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE oem.catalog_items (
    catalog_id SERIAL PRIMARY KEY,
    oem_code VARCHAR(10) NOT NULL REFERENCES oem.brands(oem_code),
    part_number VARCHAR(30) NOT NULL,
    part_number_type VARCHAR(15) CHECK (part_number_type IN ('BASIC_5', 'DESIGN_5', 'FULL_12')),
    description_es TEXT,
    description_en TEXT,
    group_code VARCHAR(20) REFERENCES cat.taxonomy_groups(group_code),
    weight_kg DECIMAL(8,3) CHECK (weight_kg >= 0),
    dimensions VARCHAR(100),
    material VARCHAR(50),
    vin_patterns TEXT[],
    model_codes TEXT[],
    body_codes TEXT[],
    engine_codes TEXT[],
    transmission_codes TEXT[],
    axle_codes TEXT[],
    color_codes TEXT[],
    trim_codes TEXT[],
    manual_types VARCHAR(20)[],
    manual_refs TEXT[],
    list_price DECIMAL(10,2) CHECK (list_price >= 0),
    net_price DECIMAL(10,2) CHECK (net_price >= 0),
    currency_code VARCHAR(3) DEFAULT 'USD',
    oem_lead_time_days INT CHECK (oem_lead_time_days >= 0),
    is_discontinued BOOLEAN DEFAULT FALSE,
    valid_from DATE CHECK (valid_from <= COALESCE(valid_until, '9999-12-31')),
    valid_until DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(oem_code, part_number)
);

CREATE TABLE oem.equivalences (
    equivalence_id SERIAL PRIMARY KEY,
    oem_part_number VARCHAR(30) NOT NULL,
    oem_code VARCHAR(10) NOT NULL,
    aftermarket_sku VARCHAR(20) REFERENCES inv.product_master(internal_sku),
    equivalence_type VARCHAR(20) CHECK (equivalence_type IN ('DIRECT', 'COMPATIBLE', 'UPGRADE', 'DOWNGRADE')),
    confidence_score INT CHECK (confidence_score BETWEEN 0 AND 100),
    notes TEXT,
    verified_by INT REFERENCES cat.technicians(technician_id),
    verified_date DATE CHECK (verified_date <= CURRENT_DATE),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(oem_part_number, oem_code, aftermarket_sku)
);

-- =====================================================
-- 3. INVENTARIO - CON PARTICIONES Y AUDITORÍA
-- =====================================================
CREATE TABLE inv.product_master (
    internal_sku VARCHAR(20) PRIMARY KEY,
    group_code VARCHAR(20) NOT NULL REFERENCES cat.taxonomy_groups(group_code),
    name VARCHAR(150) NOT NULL,
    description TEXT,
    brand VARCHAR(50),
    oem_ref VARCHAR(30),
    oem_code VARCHAR(10) REFERENCES oem.brands(oem_code),
    source_code VARCHAR(10) NOT NULL REFERENCES cat.source_codes(source_code),
    condition_code VARCHAR(10) NOT NULL REFERENCES cat.condition_codes(condition_code),
    position_code VARCHAR(10) REFERENCES cat.position_codes(position_code),
    finish_code VARCHAR(10) REFERENCES cat.finish_codes(finish_code),
    color_code VARCHAR(10) REFERENCES cat.color_codes(color_code),
    uom_code VARCHAR(10) NOT NULL REFERENCES cat.uom_codes(uom_code),
    barcode VARCHAR(50),
    supplier_mpn VARCHAR(50),
    interchange_numbers JSONB DEFAULT '[]',
    cross_references JSONB DEFAULT '[]',
    weight_kg DECIMAL(8,3) CHECK (weight_kg >= 0),
    dimensions_cm VARCHAR(50),
    package_qty INTEGER DEFAULT 1 CHECK (package_qty > 0),
    min_stock INTEGER DEFAULT 0 CHECK (min_stock >= 0),
    max_stock INTEGER DEFAULT 1000 CHECK (max_stock >= min_stock),
    reorder_point INTEGER DEFAULT 0 CHECK (reorder_point >= 0),
    safety_stock INTEGER DEFAULT 0 CHECK (safety_stock >= 0),
    lead_time_days INTEGER DEFAULT 7 CHECK (lead_time_days >= 0),
    core_required BOOLEAN DEFAULT FALSE,
    core_price DECIMAL(10,2) DEFAULT 0 CHECK (core_price >= 0),
    warranty_days INTEGER DEFAULT 90 CHECK (warranty_days >= 0),
    standard_cost DECIMAL(10,2) DEFAULT 0 CHECK (standard_cost >= 0),
    avg_cost DECIMAL(10,2) DEFAULT 0 CHECK (avg_cost >= 0),
    last_purchase_cost DECIMAL(10,2) DEFAULT 0 CHECK (last_purchase_cost >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    is_serialized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE inv.warehouses (
    warehouse_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) CHECK (type IN ('MAIN', 'SATELLITE', 'COUNTER', 'QUARANTINE', 'RETURNS')),
    address TEXT,
    contact_phone VARCHAR(20),
    manager VARCHAR(100),
    capacity INT CHECK (capacity >= 0),
    current_occupancy INT DEFAULT 0 CHECK (current_occupancy >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE inv.bins (
    bin_id SERIAL PRIMARY KEY,
    warehouse_code VARCHAR(20) NOT NULL REFERENCES inv.warehouses(warehouse_code) ON DELETE CASCADE,
    bin_code VARCHAR(30) NOT NULL,
    description VARCHAR(100),
    zone VARCHAR(30),
    aisle VARCHAR(10),
    rack VARCHAR(10),
    level VARCHAR(10),
    position VARCHAR(10),
    capacity INT CHECK (capacity >= 0),
    max_weight_kg DECIMAL(8,2) CHECK (max_weight_kg >= 0),
    current_occupancy INT DEFAULT 0 CHECK (current_occupancy >= 0),
    temperature_zone VARCHAR(20),
    hazard_level VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(warehouse_code, bin_code),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla particionada para stock
CREATE TABLE inv.stock (
    stock_id BIGSERIAL,
    internal_sku VARCHAR(20) NOT NULL REFERENCES inv.product_master(internal_sku) ON DELETE CASCADE,
    warehouse_code VARCHAR(20) NOT NULL REFERENCES inv.warehouses(warehouse_code) ON DELETE CASCADE,
    bin_id INT REFERENCES inv.bins(bin_id) ON DELETE SET NULL,
    qty_on_hand INTEGER NOT NULL DEFAULT 0 CHECK (qty_on_hand >= 0),
    qty_reserved INTEGER NOT NULL DEFAULT 0 CHECK (qty_reserved >= 0),
    qty_available INTEGER GENERATED ALWAYS AS (qty_on_hand - qty_reserved) STORED,
    qty_on_order INTEGER DEFAULT 0 CHECK (qty_on_order >= 0),
    batch_number VARCHAR(50),
    serial_number VARCHAR(100),
    expiration_date DATE CHECK (expiration_date > manufacturing_date),
    manufacturing_date DATE CHECK (manufacturing_date <= CURRENT_DATE),
    unit_cost DECIMAL(10,2) DEFAULT 0 CHECK (unit_cost >= 0),
    total_cost DECIMAL(12,2) GENERATED ALWAYS AS (qty_on_hand * unit_cost) STORED,
    last_receipt_date DATE NOT NULL DEFAULT CURRENT_DATE CHECK (last_receipt_date <= CURRENT_DATE),
    last_count_date DATE CHECK (last_count_date <= CURRENT_DATE),
    next_count_date DATE CHECK (next_count_date >= CURRENT_DATE),
    status VARCHAR(20) DEFAULT 'AVAILABLE' CHECK (status IN ('AVAILABLE', 'RESERVED', 'QUARANTINE', 'DAMAGED', 'SOLD')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    PRIMARY KEY (stock_id, last_receipt_date),
    UNIQUE(internal_sku, warehouse_code, bin_id, batch_number, serial_number)
) PARTITION BY RANGE (last_receipt_date);

-- Particiones
CREATE TABLE inv.stock_2025 PARTITION OF inv.stock FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE inv.stock_2026 PARTITION OF inv.stock FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE inv.stock_default PARTITION OF inv.stock DEFAULT;

-- Tabla particionada para transacciones
CREATE TABLE inv.transactions (
    txn_id BIGSERIAL,
    txn_type VARCHAR(20) NOT NULL CHECK (txn_type IN ('IN', 'OUT', 'TRANSFER', 'ADJUST', 'RESERVE', 'RELEASE', 'COUNT')),
    txn_date TIMESTAMP NOT NULL DEFAULT NOW() CHECK (txn_date <= CURRENT_TIMESTAMP),
    internal_sku VARCHAR(20) NOT NULL REFERENCES inv.product_master(internal_sku),
    qty INTEGER NOT NULL CHECK (qty != 0),
    uom_code VARCHAR(10) REFERENCES cat.uom_codes(uom_code),
    from_warehouse VARCHAR(20) REFERENCES inv.warehouses(warehouse_code),
    from_bin VARCHAR(30),
    to_warehouse VARCHAR(20) REFERENCES inv.warehouses(warehouse_code),
    to_bin VARCHAR(30),
    unit_cost DECIMAL(10,2) CHECK (unit_cost >= 0),
    total_cost DECIMAL(12,2) GENERATED ALWAYS AS (qty * unit_cost) STORED,
    reference_number VARCHAR(50),
    reference_type VARCHAR(20),
    work_order_id INT REFERENCES svc.work_orders(wo_id) ON DELETE SET NULL,
    purchase_order_id INT REFERENCES inv.purchase_orders(po_id) ON DELETE SET NULL,
    sales_order_id INT,
    performed_by INT REFERENCES cat.technicians(technician_id),
    approved_by INT REFERENCES cat.technicians(technician_id),
    created_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    PRIMARY KEY (txn_id, txn_date),
    CONSTRAINT chk_transfer CHECK (
        (txn_type = 'TRANSFER' AND from_warehouse IS NOT NULL AND to_warehouse IS NOT NULL) OR
        (txn_type != 'TRANSFER' OR (txn_type = 'TRANSFER' AND from_warehouse != to_warehouse))
    )
) PARTITION BY RANGE (txn_date);

-- Particiones
CREATE TABLE inv.transactions_2025 PARTITION OF inv.transactions FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE inv.transactions_2026 PARTITION OF inv.transactions FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE inv.transactions_default PARTITION OF inv.transactions DEFAULT;

CREATE TABLE inv.purchase_orders (
    po_id SERIAL PRIMARY KEY,
    po_number VARCHAR(30) UNIQUE NOT NULL,
    supplier_id INT NOT NULL REFERENCES cat.suppliers(supplier_id) ON DELETE SET NULL,
    order_date DATE DEFAULT CURRENT_DATE CHECK (order_date <= CURRENT_DATE),
    expected_delivery_date DATE CHECK (expected_delivery_date >= order_date),
    actual_delivery_date DATE CHECK (actual_delivery_date >= order_date),
    status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','PENDING','PARTIAL','RECEIVED','CLOSED','CANCELLED')),
    subtotal DECIMAL(12,2) DEFAULT 0 CHECK (subtotal >= 0),
    tax_amount DECIMAL(12,2) DEFAULT 0 CHECK (tax_amount >= 0),
    shipping_cost DECIMAL(10,2) DEFAULT 0 CHECK (shipping_cost >= 0),
    total_amount DECIMAL(12,2) GENERATED ALWAYS AS (subtotal + tax_amount + shipping_cost) STORED,
    created_by INT REFERENCES cat.technicians(technician_id),
    approved_by INT REFERENCES cat.technicians(technician_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE inv.po_items (
    po_item_id SERIAL PRIMARY KEY,
    po_id INT NOT NULL REFERENCES inv.purchase_orders(po_id) ON DELETE CASCADE,
    internal_sku VARCHAR(20) REFERENCES inv.product_master(internal_sku) ON DELETE SET NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    discount_percent DECIMAL(5,2) DEFAULT 0 CHECK (discount_percent BETWEEN 0 AND 100),
    tax_percent DECIMAL(5,2) DEFAULT 0 CHECK (tax_percent BETWEEN 0 AND 100),
    quantity_received INTEGER DEFAULT 0 CHECK (quantity_received >= 0),
    quantity_rejected INTEGER DEFAULT 0 CHECK (quantity_rejected >= 0),
    line_total DECIMAL(12,2) GENERATED ALWAYS AS (
        quantity * unit_price * (1 - discount_percent/100) * (1 + tax_percent/100)
    ) STORED,
    notes TEXT,
    CONSTRAINT chk_quantity_received CHECK (quantity_received <= quantity)
);

-- Listas de precios mejoradas
CREATE TABLE inv.price_lists (
    price_list_id SERIAL PRIMARY KEY,
    price_list_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    currency_code VARCHAR(3) REFERENCES cat.currencies(currency_code),
    is_tax_included BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE DEFAULT CURRENT_DATE CHECK (valid_from <= COALESCE(valid_until, '9999-12-31')),
    valid_until DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE inv.product_prices (
    product_price_id SERIAL PRIMARY KEY,
    price_list_id INT NOT NULL REFERENCES inv.price_lists(price_list_id) ON DELETE CASCADE,
    internal_sku VARCHAR(20) NOT NULL REFERENCES inv.product_master(internal_sku) ON DELETE CASCADE,
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    tax_percent DECIMAL(5,2) DEFAULT 0 CHECK (tax_percent BETWEEN 0 AND 100),
    discount_percent DECIMAL(5,2) DEFAULT 0 CHECK (discount_percent BETWEEN 0 AND 100),
    min_qty INTEGER DEFAULT 1 CHECK (min_qty > 0),
    valid_from DATE DEFAULT CURRENT_DATE CHECK (valid_from <= COALESCE(valid_until, '9999-12-31')),
    valid_until DATE,
    UNIQUE(price_list_id, internal_sku, valid_from)
);

-- =====================================================
-- 4. SERVICIO - CON CONSTRAINTS MEJORADOS
-- =====================================================
CREATE TABLE svc.flat_rate_standards (
    standard_id SERIAL PRIMARY KEY,
    service_code VARCHAR(20) UNIQUE NOT NULL,
    description_es TEXT NOT NULL,
    description_en TEXT,
    equipment_type_id INT REFERENCES cat.equipment_types(type_id),
    group_code VARCHAR(20) REFERENCES cat.taxonomy_groups(group_code),
    standard_hours DECIMAL(5,2) NOT NULL CHECK (standard_hours > 0),
    min_hours DECIMAL(5,2) CHECK (min_hours > 0),
    max_hours DECIMAL(5,2) CHECK (max_hours >= min_hours),
    difficulty_level INT CHECK (difficulty_level BETWEEN 1 AND 5),
    required_tools TEXT[],
    required_skills TEXT[],
    manual_source VARCHAR(50),
    manual_ref VARCHAR(100),
    oem_ref VARCHAR(30),
    valid_from DATE DEFAULT CURRENT_DATE CHECK (valid_from <= COALESCE(valid_until, '9999-12-31')),
    valid_until DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE svc.service_checklists (
    checklist_id SERIAL PRIMARY KEY,
    flat_rate_id INT REFERENCES svc.flat_rate_standards(standard_id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    sequence_no INTEGER NOT NULL CHECK (sequence_no > 0),
    is_critical BOOLEAN DEFAULT FALSE,
    expected_result VARCHAR(100),
    tool_required VARCHAR(100),
    estimated_minutes INTEGER CHECK (estimated_minutes > 0),
    UNIQUE(flat_rate_id, sequence_no)
);

CREATE TABLE svc.work_orders (
    wo_id SERIAL PRIMARY KEY,
    wo_number VARCHAR(30) UNIQUE NOT NULL,
    equipment_id INT NOT NULL REFERENCES cat.equipment(equipment_id) ON DELETE SET NULL,
    client_id INT NOT NULL REFERENCES cat.clients(client_id) ON DELETE SET NULL,
    appointment_date TIMESTAMP CHECK (appointment_date >= created_at),
    reception_date TIMESTAMP CHECK (reception_date >= appointment_date OR appointment_date IS NULL),
    diagnosis_date TIMESTAMP CHECK (diagnosis_date >= reception_date OR reception_date IS NULL),
    estimated_start_date TIMESTAMP CHECK (estimated_start_date >= diagnosis_date OR diagnosis_date IS NULL),
    actual_start_date TIMESTAMP CHECK (actual_start_date >= reception_date OR reception_date IS NULL),
    estimated_completion_date TIMESTAMP CHECK (estimated_completion_date >= estimated_start_date OR estimated_start_date IS NULL),
    actual_completion_date TIMESTAMP CHECK (actual_completion_date >= actual_start_date OR actual_start_date IS NULL),
    qc_date TIMESTAMP CHECK (qc_date >= actual_completion_date OR actual_completion_date IS NULL),
    delivery_date TIMESTAMP CHECK (delivery_date >= qc_date OR qc_date IS NULL),
    service_type VARCHAR(30) NOT NULL CHECK (service_type IN ('PREVENTIVO','CORRECTIVO','DIAGNÓSTICO','GARANTÍA','INSPECCIÓN')),
    customer_complaints TEXT,
    initial_findings TEXT,
    technician_notes TEXT,
    qc_notes TEXT,
    final_report TEXT,
    flat_rate_hours DECIMAL(5,2) CHECK (flat_rate_hours >= 0),
    estimated_hours DECIMAL(5,2) CHECK (estimated_hours >= 0),
    actual_hours DECIMAL(5,2) CHECK (actual_hours >= 0),
    efficiency_rate DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN actual_hours > 0 THEN (flat_rate_hours / actual_hours) * 100 
            ELSE 0 
        END
    ) STORED,
    labor_rate DECIMAL(10,2) DEFAULT 0 CHECK (labor_rate >= 0),
    labor_cost DECIMAL(10,2) GENERATED ALWAYS AS (actual_hours * labor_rate) STORED,
    parts_cost DECIMAL(10,2) DEFAULT 0 CHECK (parts_cost >= 0),
    additional_costs DECIMAL(10,2) DEFAULT 0 CHECK (additional_costs >= 0),
    total_cost DECIMAL(12,2) GENERATED ALWAYS AS (labor_cost + parts_cost + additional_costs) STORED,
    quoted_price DECIMAL(10,2) CHECK (quoted_price >= 0),
    discount_amount DECIMAL(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
    discount_percent DECIMAL(5,2) DEFAULT 0 CHECK (discount_percent BETWEEN 0 AND 100),
    final_price DECIMAL(10,2) GENERATED ALWAYS AS (
        COALESCE(quoted_price, total_cost) - discount_amount
    ) STORED,
    status VARCHAR(30) DEFAULT 'DRAFT' CHECK (status IN (
        'DRAFT','QUOTED','APPROVED','CITA','RECEPCIÓN','DIAGNÓSTICO',
        'ESPERA_REPUESTOS','EN_PROCESO','QA','FACTURACIÓN',
        'ENTREGADO','CERRADO','CANCELLED'
    )),
    priority VARCHAR(10) DEFAULT 'NORMAL' CHECK (priority IN ('URGENTE','ALTA','NORMAL','BAJA')),
    advisor_id INT REFERENCES cat.technicians(technician_id),
    technician_id INT REFERENCES cat.technicians(technician_id),
    qc_technician_id INT REFERENCES cat.technicians(technician_id),
    mileage_in INT CHECK (mileage_in >= 0),
    mileage_out INT CHECK (mileage_out >= mileage_in),
    hours_in INT CHECK (hours_in >= 0),
    hours_out INT CHECK (hours_out >= hours_in),
    created_by INT REFERENCES cat.technicians(technician_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP CHECK (closed_at >= created_at),
    notes TEXT,
    CONSTRAINT chk_wo_dates CHECK (
        (delivery_date IS NULL OR actual_completion_date IS NULL OR delivery_date >= actual_completion_date) AND
        (actual_completion_date IS NULL OR actual_start_date IS NULL OR actual_completion_date >= actual_start_date)
    )
);

CREATE TABLE svc.wo_items (
    item_id SERIAL PRIMARY KEY,
    wo_id INT NOT NULL REFERENCES svc.work_orders(wo_id) ON DELETE CASCADE,
    internal_sku VARCHAR(20) REFERENCES inv.product_master(internal_sku) ON DELETE SET NULL,
    qty_ordered DECIMAL(10,3) NOT NULL DEFAULT 1 CHECK (qty_ordered > 0),
    qty_used DECIMAL(10,3) NOT NULL DEFAULT 0 CHECK (qty_used >= 0),
    qty_returned DECIMAL(10,3) DEFAULT 0 CHECK (qty_returned >= 0),
    unit_price DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    discount_percent DECIMAL(5,2) DEFAULT 0 CHECK (discount_percent BETWEEN 0 AND 100),
    tax_percent DECIMAL(5,2) DEFAULT 0 CHECK (tax_percent BETWEEN 0 AND 100),
    line_total DECIMAL(10,2) GENERATED ALWAYS AS (
        qty_used * unit_price * (1 - discount_percent/100) * (1 + tax_percent/100)
    ) STORED,
    reserved_stock_id BIGINT REFERENCES inv.stock(stock_id),
    used_stock_id BIGINT REFERENCES inv.stock(stock_id),
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING','RESERVED','USED','RETURNED','CANCELLED')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_qty_used CHECK (qty_used <= qty_ordered + qty_returned),
    CONSTRAINT chk_stock_refs CHECK (
        (reserved_stock_id IS NOT NULL AND used_stock_id IS NULL) OR
        (used_stock_id IS NOT NULL) OR
        (reserved_stock_id IS NULL AND used_stock_id IS NULL)
    )
);

CREATE TABLE svc.wo_services (
    service_id SERIAL PRIMARY KEY,
    wo_id INT NOT NULL REFERENCES svc.work_orders(wo_id) ON DELETE CASCADE,
    flat_rate_id INT REFERENCES svc.flat_rate_standards(standard_id),
    service_code VARCHAR(20),
    description TEXT NOT NULL,
    flat_hours DECIMAL(5,2) CHECK (flat_hours >= 0),
    estimated_hours DECIMAL(5,2) CHECK (estimated_hours >= 0),
    actual_hours DECIMAL(5,2) CHECK (actual_hours >= 0),
    hourly_rate DECIMAL(10,2) CHECK (hourly_rate >= 0),
    labor_cost DECIMAL(10,2) GENERATED ALWAYS AS (actual_hours * hourly_rate) STORED,
    completion_status VARCHAR(20) DEFAULT 'PENDING' CHECK (
        completion_status IN ('PENDING','IN_PROGRESS','COMPLETED','QA_PASSED','QA_FAILED')
    ),
    technician_id INT REFERENCES cat.technicians(technician_id),
    started_at TIMESTAMP CHECK (started_at >= (SELECT created_at FROM svc.work_orders WHERE wo_id = wo_services.wo_id)),
    completed_at TIMESTAMP CHECK (completed_at >= started_at OR started_at IS NULL),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_service_hours CHECK (actual_hours <= estimated_hours * 2) -- Máximo 200% sobre estimado
);

-- =====================================================
-- 5. FACTURACIÓN - CON VALIDACIONES COMPLETAS
-- =====================================================
CREATE TABLE svc.invoices (
    invoice_id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(30) UNIQUE NOT NULL,
    wo_id INT REFERENCES svc.work_orders(wo_id) ON DELETE SET NULL,
    client_id INT NOT NULL REFERENCES cat.clients(client_id) ON DELETE RESTRICT,
    currency_code VARCHAR(3) REFERENCES cat.currencies(currency_code),
    subtotal DECIMAL(12,2) DEFAULT 0 CHECK (subtotal >= 0),
    tax_amount DECIMAL(12,2) DEFAULT 0 CHECK (tax_amount >= 0),
    discount_amount DECIMAL(12,2) DEFAULT 0 CHECK (discount_amount >= 0),
    total_amount DECIMAL(12,2) GENERATED ALWAYS AS (subtotal + tax_amount - discount_amount) STORED,
    status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','SENT','PAID','CANCELLED','OVERDUE')),
    issue_date DATE DEFAULT CURRENT_DATE CHECK (issue_date <= CURRENT_DATE),
    due_date DATE CHECK (due_date >= issue_date),
    paid_date DATE CHECK (paid_date >= issue_date),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_invoice_paid CHECK (
        (status != 'PAID' OR paid_date IS NOT NULL) AND
        (status = 'PAID' OR paid_date IS NULL)
    )
);

CREATE TABLE svc.invoice_items (
    invoice_item_id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL REFERENCES svc.invoices(invoice_id) ON DELETE CASCADE,
    internal_sku VARCHAR(20) REFERENCES inv.product_master(internal_sku),
    description TEXT NOT NULL,
    qty DECIMAL(10,3) NOT NULL CHECK (qty > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    tax_percent DECIMAL(5,2) DEFAULT 0 CHECK (tax_percent BETWEEN 0 AND 100),
    discount_percent DECIMAL(5,2) DEFAULT 0 CHECK (discount_percent BETWEEN 0 AND 100),
    line_total DECIMAL(10,2) GENERATED ALWAYS AS (
        qty * unit_price * (1 + tax_percent/100) * (1 - discount_percent/100)
    ) STORED
);

CREATE TABLE svc.payments (
    payment_id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL REFERENCES svc.invoices(invoice_id) ON DELETE CASCADE,
    payment_date DATE DEFAULT CURRENT_DATE CHECK (payment_date <= CURRENT_DATE),
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    currency_code VARCHAR(3) REFERENCES cat.currencies(currency_code),
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('CASH','CARD','TRANSFER','CHECK','OTHER')),
    reference_number VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_payment_amount CHECK (
        amount <= (SELECT total_amount FROM svc.invoices WHERE invoice_id = payments.invoice_id)
    )
);

-- =====================================================
-- 6. DOCUMENTOS - CON STORAGE MÚLTIPLE
-- =====================================================
CREATE TABLE doc.documents (
    doc_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('WORK_ORDER','EQUIPMENT','PRODUCT','CLIENT','SUPPLIER','INVOICE')),
    entity_id INT NOT NULL,
    doc_type VARCHAR(30) NOT NULL CHECK (doc_type IN (
        'RECEPCIÓN','DAÑOS','PROCESO','FINAL','FIRMA','COMPROBANTE',
        'GENERAL','SERIAL','MANUAL','DIBUJO','CERTIFICADO','GARANTÍA','FACTURA'
    )),
    storage_type VARCHAR(10) DEFAULT 'DATABASE' CHECK (storage_type IN ('DATABASE','FILESYSTEM','S3','PAPERLESS')),
    file_path TEXT,
    file_data BYTEA,
    paperless_id VARCHAR(50),
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER CHECK (file_size >= 0),
    mime_type VARCHAR(100),
    thumbnail BYTEA,
    thumbnail_size VARCHAR(20),
    title VARCHAR(200),
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    uploaded_by INT REFERENCES cat.technicians(technician_id),
    taken_by INT REFERENCES cat.technicians(technician_id),
    taken_at TIMESTAMP CHECK (taken_at <= CURRENT_TIMESTAMP),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_storage CHECK (
        (storage_type = 'DATABASE' AND file_data IS NOT NULL) OR
        (storage_type = 'FILESYSTEM' AND file_path IS NOT NULL) OR
        (storage_type = 'S3' AND file_path IS NOT NULL) OR
        (storage_type = 'PAPERLESS' AND paperless_id IS NOT NULL)
    )
);

-- =====================================================
-- 7. MÉTRICAS - CON VALIDACIONES
-- =====================================================
CREATE TABLE kpi.wo_metrics (
    metric_id SERIAL PRIMARY KEY,
    wo_id INT UNIQUE NOT NULL REFERENCES svc.work_orders(wo_id) ON DELETE CASCADE,
    efficiency_score DECIMAL(5,2) CHECK (efficiency_score BETWEEN 0 AND 200),
    productivity_score DECIMAL(5,2) CHECK (productivity_score BETWEEN 0 AND 200),
    quality_score DECIMAL(5,2) CHECK (quality_score BETWEEN 0 AND 100),
    customer_satisfaction DECIMAL(5,2) CHECK (customer_satisfaction BETWEEN 0 AND 100),
    lead_time_days DECIMAL(5,2) CHECK (lead_time_days >= 0),
    process_time_days DECIMAL(5,2) CHECK (process_time_days >= 0),
    wait_time_days DECIMAL(5,2) CHECK (wait_time_days >= 0),
    parts_fill_rate DECIMAL(5,2) CHECK (parts_fill_rate BETWEEN 0 AND 100),
    parts_accuracy DECIMAL(5,2) CHECK (parts_accuracy BETWEEN 0 AND 100),
    return_rate DECIMAL(5,2) CHECK (return_rate BETWEEN 0 AND 100),
    profitability DECIMAL(5,2),
    labor_utilization DECIMAL(5,2) CHECK (labor_utilization BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 8. APP - REGLAS, ALERTAS Y AUDITORÍA PARTICIONADA
-- =====================================================
CREATE TABLE app.business_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_code VARCHAR(30) UNIQUE NOT NULL,
    rule_name VARCHAR(100) NOT NULL,
    condition_text TEXT NOT NULL,
    condition_type VARCHAR(20) DEFAULT 'SQL' CHECK (condition_type IN ('SQL','EXPRESSION','FUNCTION')),
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('VALIDATE','ALERT','AUTO_CORRECT','LOG','BLOCK')),
    action_text TEXT NOT NULL,
    applies_to_table VARCHAR(50),
    applies_to_schema VARCHAR(20),
    trigger_event VARCHAR(20) CHECK (trigger_event IN ('INSERT','UPDATE','DELETE','ANY')),
    severity VARCHAR(10) DEFAULT 'MEDIUM' CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    is_active BOOLEAN DEFAULT TRUE,
    is_system_rule BOOLEAN DEFAULT FALSE,
    execution_order INT DEFAULT 10,
    stop_on_match BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE app.alerts (
    alert_id SERIAL PRIMARY KEY,
    alert_type VARCHAR(30) NOT NULL CHECK (alert_type IN (
        'STOCK_LOW','STOCK_OUT','REORDER_NEEDED','WO_DELAYED','WO_OVERDUE',
        'WO_QA_FAILED','CLIENT_CREDIT','SUPPLIER_DELAY','SYSTEM_ERROR','MAINTENANCE_DUE'
    )),
    ref_entity VARCHAR(30),
    ref_id INT,
    ref_code VARCHAR(50),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    severity VARCHAR(10) DEFAULT 'MEDIUM' CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    status VARCHAR(20) DEFAULT 'NEW' CHECK (status IN ('NEW','READ','ACKNOWLEDGED','RESOLVED','DISMISSED')),
    assigned_to INT REFERENCES cat.technicians(technician_id),
    created_for INT REFERENCES cat.technicians(technician_id),
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    CONSTRAINT chk_alert_dates CHECK (
        (read_at IS NULL OR read_at >= created_at) AND
        (acknowledged_at IS NULL OR acknowledged_at >= created_at) AND
        (resolved_at IS NULL OR resolved_at >= created_at)
    )
);

-- Tabla particionada de auditoría
CREATE TABLE app.audit_logs (
    audit_id BIGSERIAL,
    table_name VARCHAR(50) NOT NULL,
    record_id BIGINT NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    changed_by INT REFERENCES cat.technicians(technician_id),
    changed_at TIMESTAMP DEFAULT NOW() CHECK (changed_at <= CURRENT_TIMESTAMP),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    PRIMARY KEY (audit_id, changed_at)
) PARTITION BY RANGE (changed_at);

-- Particiones de auditoría
CREATE TABLE app.audit_logs_2025 PARTITION OF app.audit_logs FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE app.audit_logs_2026 PARTITION OF app.audit_logs FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE app.audit_logs_default PARTITION OF app.audit_logs DEFAULT;

-- =====================================================
-- 9. ÍNDICES COMPLETOS - TODOS LOS DE AMBAS VERSIONES
-- =====================================================

-- Índices para catálogos
CREATE INDEX idx_equipment_search ON cat.equipment 
    USING GIN (to_tsvector('spanish', 
        COALESCE(brand,'') || ' ' || 
        COALESCE(model,'') || ' ' || 
        COALESCE(vin,'') || ' ' || 
        COALESCE(license_plate,'')
    ));
CREATE INDEX idx_equipment_brand_model ON cat.equipment(brand, model, year);
CREATE INDEX idx_equipment_vin ON cat.equipment(vin) WHERE vin IS NOT NULL;
CREATE INDEX idx_equipment_license ON cat.equipment(license_plate) WHERE license_plate IS NOT NULL;
CREATE INDEX idx_equipment_client_status ON cat.equipment(client_id, status);
CREATE INDEX idx_equipment_custom_gin ON cat.equipment USING GIN (custom_fields);

CREATE INDEX idx_clients_name_trgm ON cat.clients USING GIN (name gin_trgm_ops);
CREATE INDEX idx_clients_tax_id ON cat.clients(tax_id);
CREATE INDEX idx_clients_status ON cat.clients(status);
CREATE INDEX idx_clients_email ON cat.clients(email) WHERE email IS NOT NULL;

CREATE INDEX idx_technicians_names ON cat.technicians(first_name, last_name);
CREATE INDEX idx_technicians_specialization ON cat.technicians USING GIN (specialization);
CREATE INDEX idx_technicians_status ON cat.technicians(status) WHERE is_active = TRUE;

CREATE INDEX idx_taxonomy_subsystems_system ON cat.taxonomy_subsystems(system_code);
CREATE INDEX idx_taxonomy_groups_subsystem ON cat.taxonomy_groups(subsystem_code);
CREATE INDEX idx_taxonomy_groups_keywords ON cat.taxonomy_groups USING GIN (keywords gin_trgm_ops);
CREATE INDEX idx_taxonomy_groups_full_path ON cat.taxonomy_groups(full_path);

-- Índices para inventario
CREATE INDEX idx_product_search ON inv.product_master 
    USING GIN (to_tsvector('spanish', 
        COALESCE(name,'') || ' ' || 
        COALESCE(description,'') || ' ' || 
        COALESCE(brand,'') || ' ' || 
        COALESCE(oem_ref,'')
    ));
CREATE INDEX idx_product_group ON inv.product_master(group_code);
CREATE INDEX idx_product_brand ON inv.product_master(brand);
CREATE INDEX idx_product_oem_ref ON inv.product_master(oem_ref);
CREATE INDEX idx_product_active ON inv.product_master(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_product_reorder ON inv.product_master(reorder_point, min_stock) WHERE is_active = TRUE;

CREATE INDEX idx_stock_sku_warehouse ON inv.stock(internal_sku, warehouse_code);
CREATE INDEX idx_stock_bin ON inv.stock(bin_id) WHERE bin_id IS NOT NULL;
CREATE INDEX idx_stock_low ON inv.stock(qty_available) WHERE qty_available < 5;
CREATE INDEX idx_stock_status ON inv.stock(status) WHERE status IN ('AVAILABLE', 'RESERVED');
CREATE INDEX idx_stock_brin_date ON inv.stock USING BRIN(last_receipt_date);

CREATE INDEX idx_transactions_sku_date ON inv.transactions(internal_sku, txn_date DESC);
CREATE INDEX idx_transactions_reference ON inv.transactions(reference_number, reference_type);
CREATE INDEX idx_transactions_type_date ON inv.transactions(txn_type, txn_date);
CREATE INDEX idx_transactions_work_order ON inv.transactions(work_order_id) WHERE work_order_id IS NOT NULL;
CREATE INDEX idx_transactions_purchase_order ON inv.transactions(purchase_order_id) WHERE purchase_order_id IS NOT NULL;
CREATE INDEX idx_transactions_brin_date ON inv.transactions USING BRIN(txn_date);

CREATE INDEX idx_po_items_received ON inv.po_items(quantity_received DESC);
CREATE INDEX idx_po_items_sku ON inv.po_items(internal_sku);

CREATE INDEX idx_price_lists_active ON inv.price_lists(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_product_prices_active ON inv.product_prices(price_list_id, internal_sku) 
    WHERE valid_until IS NULL OR valid_until >= CURRENT_DATE;
CREATE INDEX idx_product_prices_sku ON inv.product_prices(internal_sku, valid_from DESC);

-- Índices para servicio
CREATE INDEX idx_wo_status_dates ON svc.work_orders(status, reception_date, delivery_date);
CREATE INDEX idx_wo_client_status ON svc.work_orders(client_id, status) 
    WHERE status NOT IN ('CERRADO', 'CANCELLED');
CREATE INDEX idx_wo_equipment ON svc.work_orders(equipment_id, status);
CREATE INDEX idx_wo_created ON svc.work_orders(created_at DESC);
CREATE INDEX idx_wo_priority ON svc.work_orders(priority, created_at);
CREATE INDEX idx_wo_technician ON svc.work_orders(technician_id, status);
CREATE INDEX idx_wo_number ON svc.work_orders(wo_number);

CREATE INDEX idx_wo_items_wo ON svc.wo_items(wo_id);
CREATE INDEX idx_wo_items_sku ON svc.wo_items(internal_sku);
CREATE INDEX idx_wo_items_status ON svc.wo_items(status) WHERE status = 'PENDING';

CREATE INDEX idx_wo_services_wo ON svc.wo_services(wo_id);
CREATE INDEX idx_wo_services_technician ON svc.wo_services(technician_id, completion_status);

CREATE INDEX idx_flat_rate_equipment ON svc.flat_rate_standards(equipment_type_id, group_code);
CREATE INDEX idx_flat_rate_active ON svc.flat_rate_standards(is_active) WHERE is_active = TRUE;

CREATE INDEX idx_service_checklists_flat ON svc.service_checklists(flat_rate_id);

-- Índices para facturación
CREATE INDEX idx_invoices_client ON svc.invoices(client_id, issue_date DESC);
CREATE INDEX idx_invoices_status ON svc.invoices(status) WHERE status IN ('SENT', 'OVERDUE');
CREATE INDEX idx_invoices_wo ON svc.invoices(wo_id) WHERE wo_id IS NOT NULL;
CREATE INDEX idx_invoices_due_status ON svc.invoices(due_date, status) WHERE status = 'SENT';

CREATE INDEX idx_invoice_items_invoice ON svc.invoice_items(invoice_id);
CREATE INDEX idx_invoice_items_sku ON svc.invoice_items(internal_sku);

CREATE INDEX idx_payments_invoice ON svc.payments(invoice_id, payment_date);
CREATE INDEX idx_payments_method ON svc.payments(payment_method, payment_date);

-- Índices para documentos
CREATE INDEX idx_documents_entity ON doc.documents(entity_type, entity_id);
CREATE INDEX idx_documents_type ON doc.documents(doc_type);
CREATE INDEX idx_documents_tags ON doc.documents USING GIN (tags);
CREATE INDEX idx_documents_uploaded ON doc.documents(uploaded_by, created_at);
CREATE INDEX idx_documents_storage ON doc.documents(storage_type) WHERE storage_type != 'DATABASE';

-- Índices para métricas
CREATE INDEX idx_wo_metrics_wo ON kpi.wo_metrics(wo_id);
CREATE INDEX idx_wo_metrics_efficiency ON kpi.wo_metrics(efficiency_score DESC) WHERE efficiency_score > 0;
CREATE INDEX idx_wo_metrics_quality ON kpi.wo_metrics(quality_score DESC) WHERE quality_score > 0;

-- Índices para app
CREATE INDEX idx_business_rules_active ON app.business_rules(is_active, execution_order) WHERE is_active = TRUE;
CREATE INDEX idx_business_rules_table ON app.business_rules(applies_to_table, trigger_event);

CREATE INDEX idx_alerts_status ON app.alerts(status, created_at DESC);
CREATE INDEX idx_alerts_assigned ON app.alerts(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX idx_alerts_ref ON app.alerts(ref_entity, ref_id);
CREATE INDEX idx_alerts_severity ON app.alerts(severity, created_at) WHERE status = 'NEW';

CREATE INDEX idx_audit_logs_table ON app.audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_dates ON app.audit_logs(changed_at DESC);
CREATE INDEX idx_audit_logs_user ON app.audit_logs(changed_by, changed_at DESC);
CREATE INDEX idx_audit_logs_action ON app.audit_logs(action, changed_at);
CREATE INDEX idx_audit_logs_brin_date ON app.audit_logs USING BRIN(changed_at);

-- Índices para OEM
CREATE INDEX idx_catalog_items_oem ON oem.catalog_items(oem_code, part_number);
CREATE INDEX idx_catalog_items_group ON oem.catalog_items(group_code);
CREATE INDEX idx_catalog_items_active ON oem.catalog_items(is_discontinued) WHERE is_discontinued = FALSE;

CREATE INDEX idx_equivalences_oem ON oem.equivalences(oem_part_number, oem_code);
CREATE INDEX idx_equivalences_sku ON oem.equivalences(aftermarket_sku);
CREATE INDEX idx_equivalences_confidence ON oem.equivalences(confidence_score DESC) WHERE confidence_score > 80;

-- =====================================================
-- 10. TRIGGERS COMPLETOS - DE AMBAS VERSIONES
-- =====================================================

-- Función para actualizar updated_at
CREATE OR REPLACE FUNCTION app.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función para generar número de OT
CREATE OR REPLACE FUNCTION svc.generate_wo_number()
RETURNS TRIGGER AS $$
DECLARE
    month_code VARCHAR(6);
    seq_num INT;
BEGIN
    month_code := TO_CHAR(NOW(), 'YYYYMM');
    
    SELECT COALESCE(MAX(SUBSTRING(wo_number FROM 10)::INT), 0) + 1
    INTO seq_num
    FROM svc.work_orders
    WHERE wo_number LIKE 'WO-' || month_code || '-%';
    
    NEW.wo_number := 'WO-' || month_code || '-' || LPAD(seq_num::TEXT, 4, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función para validar reglas de negocio
CREATE OR REPLACE FUNCTION app.validate_business_rules()
RETURNS TRIGGER AS $$
DECLARE
    rule RECORD;
    condition_result BOOLEAN;
BEGIN
    FOR rule IN 
        SELECT * FROM app.business_rules 
        WHERE is_active = TRUE 
        AND applies_to_table = TG_TABLE_NAME
        ORDER BY execution_order 
    LOOP
        IF rule.condition_type = 'SQL' THEN
            EXECUTE 'SELECT EXISTS (SELECT 1 FROM ' || TG_TABLE_NAME || 
                    ' WHERE ' || rule.condition_text || ' AND ' || 
                    TG_TABLE_NAME || '_id = $1)' 
            INTO condition_result 
            USING NEW;
            
            IF condition_result THEN
                CASE rule.action_type
                    WHEN 'BLOCK' THEN 
                        RAISE EXCEPTION 'Regla de negocio violada: %', rule.rule_name;
                    WHEN 'ALERT' THEN 
                        INSERT INTO app.alerts (alert_type, title, message, ref_entity, ref_id)
                        VALUES ('SYSTEM_ERROR', 'Regla de negocio', rule.rule_name, 
                                TG_TABLE_NAME, NEW.wo_id);
                END CASE;
                
                IF rule.stop_on_match THEN
                    EXIT;
                END IF;
            END IF;
        END IF;
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función CORREGIDA: Update stock on transaction
CREATE OR REPLACE FUNCTION inv.update_stock_on_transaction()
RETURNS TRIGGER AS $$
BEGIN
    -- 🔴 CORRECCIÓN CRÍTICA: Usar nombres correctos de columnas
    IF NEW.txn_type IN ('IN','TRANSFER') THEN
        UPDATE inv.stock 
        SET qty_on_hand = qty_on_hand + ABS(NEW.qty),
            updated_at = NOW()
        WHERE internal_sku = NEW.internal_sku 
        AND warehouse_code = COALESCE(NEW.to_warehouse, NEW.from_warehouse);
    ELSIF NEW.txn_type IN ('OUT','ADJUST') THEN
        UPDATE inv.stock 
        SET qty_on_hand = qty_on_hand - ABS(NEW.qty),
            updated_at = NOW()
        WHERE internal_sku = NEW.internal_sku 
        AND warehouse_code = COALESCE(NEW.from_warehouse, NEW.to_warehouse);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función de auditoría
CREATE OR REPLACE FUNCTION app.audit_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_record_id BIGINT;
BEGIN
    -- Determinar el ID del registro
    IF TG_OP = 'INSERT' THEN
        v_record_id := NEW.wo_id;
    ELSIF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
        v_record_id := OLD.wo_id;
    END IF;
    
    -- Insertar registro de auditoría
    INSERT INTO app.audit_logs (table_name, record_id, action, changed_by, old_values, new_values)
    VALUES (
        TG_TABLE_NAME,
        v_record_id,
        TG_OP,
        current_setting('app.user_id', TRUE)::INT,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función para generar factura al entregar
CREATE OR REPLACE FUNCTION svc.gen_invoice_on_delivery()
RETURNS TRIGGER AS $$
DECLARE
    v_invoice_number VARCHAR(30);
BEGIN
    IF NEW.delivery_date IS NOT NULL AND OLD.delivery_date IS NULL THEN
        -- Generar número de factura
        v_invoice_number := 'INV-' || TO_CHAR(NOW(), 'YYYYMM') || '-' || 
                           LPAD((SELECT COUNT(*) + 1 FROM svc.invoices 
                                 WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM NOW())
                                 AND EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM NOW()))::TEXT, 4, '0');
        
        -- Crear factura
        INSERT INTO svc.invoices (invoice_number, wo_id, client_id, subtotal, total_amount, status, issue_date, due_date)
        VALUES (
            v_invoice_number,
            NEW.wo_id,
            NEW.client_id,
            NEW.total_cost,
            NEW.total_cost,
            'SENT',
            CURRENT_DATE,
            CURRENT_DATE + 30
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar inventario automáticamente
CREATE OR REPLACE FUNCTION inv.auto_update_inventory()
RETURNS TRIGGER AS $$
BEGIN
    -- Actualizar stock cuando se usa un item en WO
    IF NEW.status = 'USED' AND OLD.status != 'USED' THEN
        UPDATE inv.stock 
        SET qty_reserved = qty_reserved - NEW.qty_used,
            qty_on_hand = qty_on_hand - NEW.qty_used,
            updated_at = NOW()
        WHERE stock_id = NEW.reserved_stock_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers aplicados
-- Triggers para updated_at
CREATE TRIGGER trg_update_equipment_updated 
    BEFORE UPDATE ON cat.equipment 
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at();

CREATE TRIGGER trg_update_client_updated 
    BEFORE UPDATE ON cat.clients 
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at();

CREATE TRIGGER trg_update_wo_updated 
    BEFORE UPDATE ON svc.work_orders 
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at();

CREATE TRIGGER trg_update_product_updated 
    BEFORE UPDATE ON inv.product_master 
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at();

CREATE TRIGGER trg_update_invoice_updated 
    BEFORE UPDATE ON svc.invoices 
    FOR EACH ROW EXECUTE FUNCTION app.update_updated_at();

-- Trigger para generar número de OT
CREATE TRIGGER trg_generate_wo_number 
    BEFORE INSERT ON svc.work_orders 
    FOR EACH ROW EXECUTE FUNCTION svc.generate_wo_number();

-- Trigger para validar reglas en OT
CREATE TRIGGER trg_validate_wo_rules 
    BEFORE INSERT OR UPDATE ON svc.work_orders 
    FOR EACH ROW EXECUTE FUNCTION app.validate_business_rules();

-- Trigger para actualizar stock en transacciones
CREATE TRIGGER trg_inv_txn_stock 
    AFTER INSERT OR UPDATE OF qty ON inv.transactions 
    FOR EACH ROW EXECUTE FUNCTION inv.update_stock_on_transaction();

-- Triggers de auditoría
CREATE TRIGGER trg_audit_wo 
    AFTER INSERT OR UPDATE OR DELETE ON svc.work_orders 
    FOR EACH ROW EXECUTE FUNCTION app.audit_changes();

CREATE TRIGGER trg_audit_invoice 
    AFTER INSERT OR UPDATE OR DELETE ON svc.invoices 
    FOR EACH ROW EXECUTE FUNCTION app.audit_changes();

CREATE TRIGGER trg_audit_stock 
    AFTER INSERT OR UPDATE OR DELETE ON inv.stock 
    FOR EACH ROW EXECUTE FUNCTION app.audit_changes();

-- Trigger para generar factura automática
CREATE TRIGGER trg_svc_delivery_invoice 
    AFTER UPDATE OF delivery_date ON svc.work_orders 
    FOR EACH ROW EXECUTE FUNCTION svc.gen_invoice_on_delivery();

-- Trigger para actualizar inventario desde WO items
CREATE TRIGGER trg_update_inventory_from_wo 
    AFTER UPDATE OF status ON svc.wo_items 
    FOR EACH ROW EXECUTE FUNCTION inv.auto_update_inventory();

-- Trigger para validar stock al reservar
CREATE OR REPLACE FUNCTION inv.validate_stock_reservation()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'RESERVED' THEN
        -- Verificar que haya stock disponible
        IF NOT EXISTS (
            SELECT 1 FROM inv.stock 
            WHERE stock_id = NEW.reserved_stock_id 
            AND qty_available >= NEW.qty_ordered
        ) THEN
            RAISE EXCEPTION 'Stock insuficiente para reservar. Disponible: %, Solicitado: %',
                (SELECT qty_available FROM inv.stock WHERE stock_id = NEW.reserved_stock_id),
                NEW.qty_ordered;
        END IF;
        
        -- Reservar el stock
        UPDATE inv.stock 
        SET qty_reserved = qty_reserved + NEW.qty_ordered,
            updated_at = NOW()
        WHERE stock_id = NEW.reserved_stock_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_stock_reservation 
    BEFORE INSERT OR UPDATE OF status ON svc.wo_items 
    FOR EACH ROW EXECUTE FUNCTION inv.validate_stock_reservation();