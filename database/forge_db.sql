
BEGIN;

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



CREATE TABLE IF NOT EXISTS app.alerts
(
    alert_id serial NOT NULL,
    alert_type character varying(30) COLLATE pg_catalog."default" NOT NULL,
    ref_entity character varying(30) COLLATE pg_catalog."default",
    ref_id integer,
    ref_code character varying(50) COLLATE pg_catalog."default",
    title character varying(200) COLLATE pg_catalog."default" NOT NULL,
    message text COLLATE pg_catalog."default" NOT NULL,
    details jsonb DEFAULT '{}'::jsonb,
    severity character varying(10) COLLATE pg_catalog."default" DEFAULT 'MEDIUM'::character varying,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'NEW'::character varying,
    assigned_to integer,
    created_for integer,
    created_at timestamp without time zone DEFAULT now(),
    read_at timestamp without time zone,
    acknowledged_at timestamp without time zone,
    resolved_at timestamp without time zone,
    CONSTRAINT alerts_pkey PRIMARY KEY (alert_id)
);

CREATE TABLE IF NOT EXISTS app.audit_logs
(
    audit_id bigserial NOT NULL,
    table_name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    record_id bigint NOT NULL,
    action character varying(10) COLLATE pg_catalog."default" NOT NULL,
    changed_by integer,
    changed_at timestamp without time zone NOT NULL DEFAULT now(),
    old_values jsonb,
    new_values jsonb,
    ip_address inet,
    user_agent text COLLATE pg_catalog."default",
    CONSTRAINT audit_logs_pkey PRIMARY KEY (audit_id, changed_at)
);

CREATE TABLE IF NOT EXISTS app.business_rules
(
    rule_id serial NOT NULL,
    rule_code character varying(30) COLLATE pg_catalog."default" NOT NULL,
    rule_name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    condition_text text COLLATE pg_catalog."default" NOT NULL,
    condition_type character varying(20) COLLATE pg_catalog."default" DEFAULT 'SQL'::character varying,
    action_type character varying(20) COLLATE pg_catalog."default" NOT NULL,
    action_text text COLLATE pg_catalog."default" NOT NULL,
    applies_to_table character varying(50) COLLATE pg_catalog."default",
    applies_to_schema character varying(20) COLLATE pg_catalog."default",
    trigger_event character varying(20) COLLATE pg_catalog."default",
    severity character varying(10) COLLATE pg_catalog."default" DEFAULT 'MEDIUM'::character varying,
    is_active boolean DEFAULT true,
    is_system_rule boolean DEFAULT false,
    execution_order integer DEFAULT 10,
    stop_on_match boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    notes text COLLATE pg_catalog."default",
    CONSTRAINT business_rules_pkey PRIMARY KEY (rule_id),
    CONSTRAINT business_rules_rule_code_key UNIQUE (rule_code)
);

CREATE TABLE IF NOT EXISTS cat.aspiration_codes
(
    aspiration_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(30) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(30) COLLATE pg_catalog."default",
    CONSTRAINT aspiration_codes_pkey PRIMARY KEY (aspiration_code)
);

CREATE TABLE IF NOT EXISTS cat.clients
(
    client_id serial NOT NULL,
    uuid uuid NOT NULL DEFAULT gen_random_uuid(),
    client_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    type character varying(15) COLLATE pg_catalog."default" NOT NULL,
    name character varying(150) COLLATE pg_catalog."default" NOT NULL,
    legal_name character varying(150) COLLATE pg_catalog."default",
    tax_id character varying(30) COLLATE pg_catalog."default",
    email character varying(100) COLLATE pg_catalog."default",
    phone character varying(30) COLLATE pg_catalog."default",
    mobile character varying(30) COLLATE pg_catalog."default",
    address text COLLATE pg_catalog."default",
    city character varying(50) COLLATE pg_catalog."default",
    state character varying(50) COLLATE pg_catalog."default",
    country character varying(50) COLLATE pg_catalog."default",
    postal_code character varying(20) COLLATE pg_catalog."default",
    credit_limit numeric(12, 2) DEFAULT 0,
    payment_days integer DEFAULT 30,
    credit_used numeric(12, 2) DEFAULT 0,
    preferred_contact_method character varying(20) COLLATE pg_catalog."default" DEFAULT 'EMAIL'::character varying,
    send_reminders boolean DEFAULT true,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'ACTIVE'::character varying,
    created_by integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    notes text COLLATE pg_catalog."default",
    CONSTRAINT clients_pkey PRIMARY KEY (client_id),
    CONSTRAINT clients_client_code_key UNIQUE (client_code),
    CONSTRAINT clients_uuid_key UNIQUE (uuid)
);

CREATE TABLE IF NOT EXISTS cat.color_codes
(
    color_id serial NOT NULL,
    color_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    brand character varying(30) COLLATE pg_catalog."default" DEFAULT 'GENERIC'::character varying,
    name_es character varying(50) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(50) COLLATE pg_catalog."default",
    hex_code character varying(7) COLLATE pg_catalog."default",
    paint_type character varying(20) COLLATE pg_catalog."default",
    is_metallic boolean DEFAULT false,
    sort_order integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT color_codes_pkey PRIMARY KEY (color_id),
    CONSTRAINT color_codes_brand_color_code_key UNIQUE (brand, color_code),
    CONSTRAINT color_codes_color_code_key UNIQUE (color_code)
);

COMMENT ON TABLE cat.color_codes
    IS 'Catálogo de colores con restricción única por código para Forge DB.';

CREATE TABLE IF NOT EXISTS cat.condition_codes
(
    condition_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(50) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(50) COLLATE pg_catalog."default",
    requires_core boolean DEFAULT false,
    sort_order integer DEFAULT 0,
    CONSTRAINT condition_codes_pkey PRIMARY KEY (condition_code)
);

CREATE TABLE IF NOT EXISTS cat.currencies
(
    currency_code character varying(3) COLLATE pg_catalog."default" NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    symbol character varying(5) COLLATE pg_catalog."default",
    exchange_rate numeric(10, 4) DEFAULT 1.0,
    decimals integer DEFAULT 2,
    is_active boolean DEFAULT true,
    CONSTRAINT currencies_pkey PRIMARY KEY (currency_code)
);

CREATE TABLE IF NOT EXISTS cat.drivetrain_codes
(
    drivetrain_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(30) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(30) COLLATE pg_catalog."default",
    CONSTRAINT drivetrain_codes_pkey PRIMARY KEY (drivetrain_code)
);

CREATE TABLE IF NOT EXISTS cat.equipment
(
    equipment_id serial NOT NULL,
    uuid uuid NOT NULL DEFAULT gen_random_uuid(),
    equipment_code character varying(40) COLLATE pg_catalog."default" NOT NULL,
    type_id integer NOT NULL,
    brand character varying(50) COLLATE pg_catalog."default" NOT NULL,
    model character varying(50) COLLATE pg_catalog."default" NOT NULL,
    year smallint,
    serial_number character varying(100) COLLATE pg_catalog."default",
    vin character varying(17) COLLATE pg_catalog."default",
    license_plate character varying(20) COLLATE pg_catalog."default",
    color character varying(30) COLLATE pg_catalog."default",
    submodel_trim character varying(40) COLLATE pg_catalog."default",
    body_style character varying(20) COLLATE pg_catalog."default",
    doors smallint,
    engine_desc character varying(100) COLLATE pg_catalog."default",
    fuel_code character varying(10) COLLATE pg_catalog."default",
    aspiration_code character varying(10) COLLATE pg_catalog."default",
    transmission_code character varying(10) COLLATE pg_catalog."default",
    drivetrain_code character varying(10) COLLATE pg_catalog."default",
    client_id integer,
    purchase_date date,
    warranty_until date,
    last_service_date date,
    next_service_date date,
    total_service_hours integer DEFAULT 0,
    total_service_cost numeric(12, 2) DEFAULT 0,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'ACTIVO'::character varying,
    current_mileage_hours integer DEFAULT 0,
    last_mileage_update date,
    custom_fields jsonb DEFAULT '{}'::jsonb,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_by integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    notes text COLLATE pg_catalog."default",
    CONSTRAINT equipment_pkey PRIMARY KEY (equipment_id),
    CONSTRAINT equipment_equipment_code_key UNIQUE (equipment_code),
    CONSTRAINT equipment_uuid_key UNIQUE (uuid)
);

CREATE TABLE IF NOT EXISTS cat.equipment_types
(
    type_id serial NOT NULL,
    type_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    category character varying(30) COLLATE pg_catalog."default" NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    icon character varying(50) COLLATE pg_catalog."default",
    color character varying(20) COLLATE pg_catalog."default",
    attr_schema jsonb DEFAULT '{}'::jsonb,
    description text COLLATE pg_catalog."default",
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT equipment_types_pkey PRIMARY KEY (type_id),
    CONSTRAINT equipment_types_type_code_key UNIQUE (type_code)
);

CREATE TABLE IF NOT EXISTS cat.finish_codes
(
    finish_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(50) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(50) COLLATE pg_catalog."default",
    requires_color boolean DEFAULT false,
    sort_order integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT finish_codes_pkey PRIMARY KEY (finish_code)
);

CREATE TABLE IF NOT EXISTS cat.fitment
(
    fitment_id serial NOT NULL,
    internal_sku character varying(20) COLLATE pg_catalog."default",
    equipment_id integer,
    score smallint DEFAULT 100,
    notes text COLLATE pg_catalog."default",
    verified_by integer,
    verified_date date,
    is_primary_fit boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT fitment_pkey PRIMARY KEY (fitment_id),
    CONSTRAINT fitment_internal_sku_equipment_id_key UNIQUE (internal_sku, equipment_id)
);

CREATE TABLE IF NOT EXISTS cat.fuel_codes
(
    fuel_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(30) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(30) COLLATE pg_catalog."default",
    is_alternative boolean DEFAULT false,
    CONSTRAINT fuel_codes_pkey PRIMARY KEY (fuel_code)
);

CREATE TABLE IF NOT EXISTS cat.position_codes
(
    position_code character varying(15) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(50) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(50) COLLATE pg_catalog."default",
    category character varying(20) COLLATE pg_catalog."default",
    sort_order integer DEFAULT 0,
    synonyms text[] COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT position_codes_pkey PRIMARY KEY (position_code)
);

CREATE TABLE IF NOT EXISTS cat.source_codes
(
    source_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(50) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(50) COLLATE pg_catalog."default",
    quality_level character varying(10) COLLATE pg_catalog."default",
    sort_order integer DEFAULT 0,
    CONSTRAINT source_codes_pkey PRIMARY KEY (source_code)
);

CREATE TABLE IF NOT EXISTS cat.suppliers
(
    supplier_id serial NOT NULL,
    supplier_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    contact_person character varying(100) COLLATE pg_catalog."default",
    contact_email character varying(100) COLLATE pg_catalog."default",
    contact_phone character varying(20) COLLATE pg_catalog."default",
    website character varying(200) COLLATE pg_catalog."default",
    address text COLLATE pg_catalog."default",
    city character varying(50) COLLATE pg_catalog."default",
    state character varying(50) COLLATE pg_catalog."default",
    country character varying(50) COLLATE pg_catalog."default",
    tax_id character varying(30) COLLATE pg_catalog."default",
    payment_terms integer DEFAULT 30,
    currency_code character varying(3) COLLATE pg_catalog."default" DEFAULT 'USD'::character varying,
    rating numeric(3, 2) DEFAULT 5.0,
    delivery_time_avg integer DEFAULT 7,
    quality_score numeric(3, 2) DEFAULT 5.0,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'ACTIVE'::character varying,
    is_preferred boolean DEFAULT false,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    notes text COLLATE pg_catalog."default",
    CONSTRAINT suppliers_pkey PRIMARY KEY (supplier_id),
    CONSTRAINT suppliers_supplier_code_key UNIQUE (supplier_code)
);

CREATE TABLE IF NOT EXISTS cat.taxonomy_groups
(
    group_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    subsystem_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    system_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(100) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(100) COLLATE pg_catalog."default",
    description text COLLATE pg_catalog."default",
    examples text COLLATE pg_catalog."default",
    keywords text COLLATE pg_catalog."default",
    requires_position boolean DEFAULT false,
    requires_color boolean DEFAULT false,
    requires_finish boolean DEFAULT false,
    requires_side boolean DEFAULT false,
    typical_position_set text COLLATE pg_catalog."default",
    typical_uom character varying(10) COLLATE pg_catalog."default",
    full_path character varying(200) COLLATE pg_catalog."default" GENERATED ALWAYS AS ((((((system_code)::text || ' > '::text) || (subsystem_code)::text) || ' > '::text) || (name_es)::text)) STORED,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT taxonomy_groups_pkey PRIMARY KEY (group_code)
);

CREATE TABLE IF NOT EXISTS cat.taxonomy_subsystems
(
    subsystem_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    system_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(100) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(100) COLLATE pg_catalog."default",
    icon character varying(50) COLLATE pg_catalog."default",
    notes text COLLATE pg_catalog."default",
    sort_order integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT taxonomy_subsystems_pkey PRIMARY KEY (subsystem_code)
);

CREATE TABLE IF NOT EXISTS cat.taxonomy_systems
(
    system_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    category character varying(30) COLLATE pg_catalog."default" DEFAULT 'AUTOMOTRIZ'::character varying,
    name_es character varying(100) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(100) COLLATE pg_catalog."default",
    icon character varying(50) COLLATE pg_catalog."default",
    scope text COLLATE pg_catalog."default",
    sort_order integer DEFAULT 0,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT taxonomy_systems_pkey PRIMARY KEY (system_code)
);

CREATE TABLE IF NOT EXISTS cat.technicians
(
    technician_id serial NOT NULL,
    employee_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    first_name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    last_name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    email character varying(100) COLLATE pg_catalog."default",
    phone character varying(20) COLLATE pg_catalog."default",
    hire_date date,
    birth_date date,
    specialization character varying(100)[] COLLATE pg_catalog."default" DEFAULT '{}'::character varying[],
    certification_level character varying(50) COLLATE pg_catalog."default",
    certifications text[] COLLATE pg_catalog."default" DEFAULT '{}'::text[],
    hourly_rate numeric(10, 2) DEFAULT 0,
    daily_rate numeric(10, 2) DEFAULT 0,
    overtime_multiplier numeric(3, 2) DEFAULT 1.5,
    work_schedule jsonb DEFAULT '{"fri": true, "mon": true, "thu": true, "tue": true, "wed": true}'::jsonb,
    efficiency_avg numeric(5, 2) DEFAULT 100.00,
    quality_score numeric(5, 2) DEFAULT 100.00,
    jobs_completed integer DEFAULT 0,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'ACTIVE'::character varying,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    notes text COLLATE pg_catalog."default",
    CONSTRAINT technicians_pkey PRIMARY KEY (technician_id),
    CONSTRAINT technicians_employee_code_key UNIQUE (employee_code)
);

CREATE TABLE IF NOT EXISTS cat.transmission_codes
(
    transmission_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(30) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(30) COLLATE pg_catalog."default",
    CONSTRAINT transmission_codes_pkey PRIMARY KEY (transmission_code)
);

CREATE TABLE IF NOT EXISTS cat.uom_codes
(
    uom_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name_es character varying(50) COLLATE pg_catalog."default" NOT NULL,
    name_en character varying(50) COLLATE pg_catalog."default",
    is_fractional boolean DEFAULT false,
    category character varying(20) COLLATE pg_catalog."default",
    CONSTRAINT uom_codes_pkey PRIMARY KEY (uom_code)
);

CREATE TABLE IF NOT EXISTS doc.documents
(
    doc_id serial NOT NULL,
    entity_type character varying(20) COLLATE pg_catalog."default" NOT NULL,
    entity_id integer NOT NULL,
    doc_type character varying(30) COLLATE pg_catalog."default" NOT NULL,
    storage_type character varying(10) COLLATE pg_catalog."default" DEFAULT 'DATABASE'::character varying,
    file_path text COLLATE pg_catalog."default",
    file_data bytea,
    paperless_id character varying(50) COLLATE pg_catalog."default",
    file_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    file_size integer,
    mime_type character varying(100) COLLATE pg_catalog."default",
    thumbnail bytea,
    thumbnail_size character varying(20) COLLATE pg_catalog."default",
    title character varying(200) COLLATE pg_catalog."default",
    description text COLLATE pg_catalog."default",
    tags text[] COLLATE pg_catalog."default" DEFAULT '{}'::text[],
    uploaded_by integer,
    taken_by integer,
    taken_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT documents_pkey PRIMARY KEY (doc_id)
);

CREATE TABLE IF NOT EXISTS inv.bins
(
    bin_id serial NOT NULL,
    warehouse_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    bin_code character varying(30) COLLATE pg_catalog."default" NOT NULL,
    description character varying(100) COLLATE pg_catalog."default",
    zone character varying(30) COLLATE pg_catalog."default",
    aisle character varying(10) COLLATE pg_catalog."default",
    rack character varying(10) COLLATE pg_catalog."default",
    level character varying(10) COLLATE pg_catalog."default",
    "position" character varying(10) COLLATE pg_catalog."default",
    capacity integer,
    max_weight_kg numeric(8, 2),
    current_occupancy integer DEFAULT 0,
    temperature_zone character varying(20) COLLATE pg_catalog."default",
    hazard_level character varying(20) COLLATE pg_catalog."default",
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT bins_pkey PRIMARY KEY (bin_id),
    CONSTRAINT bins_warehouse_code_bin_code_key UNIQUE (warehouse_code, bin_code)
);

CREATE TABLE IF NOT EXISTS inv.po_items
(
    po_item_id serial NOT NULL,
    po_id integer NOT NULL,
    internal_sku character varying(20) COLLATE pg_catalog."default",
    quantity integer NOT NULL,
    unit_price numeric(10, 2) NOT NULL,
    discount_percent numeric(5, 2) DEFAULT 0,
    tax_percent numeric(5, 2) DEFAULT 0,
    quantity_received integer DEFAULT 0,
    quantity_rejected integer DEFAULT 0,
    line_total numeric(12, 2) GENERATED ALWAYS AS (((((quantity)::numeric * unit_price) * ((1)::numeric - (discount_percent / (100)::numeric))) * ((1)::numeric + (tax_percent / (100)::numeric)))) STORED,
    notes text COLLATE pg_catalog."default",
    CONSTRAINT po_items_pkey PRIMARY KEY (po_item_id)
);

CREATE TABLE IF NOT EXISTS inv.price_lists
(
    price_list_id serial NOT NULL,
    price_list_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    description text COLLATE pg_catalog."default",
    currency_code character varying(3) COLLATE pg_catalog."default",
    is_tax_included boolean DEFAULT false,
    is_active boolean DEFAULT true,
    valid_from date DEFAULT CURRENT_DATE,
    valid_until date,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT price_lists_pkey PRIMARY KEY (price_list_id),
    CONSTRAINT price_lists_price_list_code_key UNIQUE (price_list_code)
);

CREATE TABLE IF NOT EXISTS inv.product_master
(
    internal_sku character varying(20) COLLATE pg_catalog."default" NOT NULL,
    group_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    name character varying(150) COLLATE pg_catalog."default" NOT NULL,
    description text COLLATE pg_catalog."default",
    brand character varying(50) COLLATE pg_catalog."default",
    oem_ref character varying(30) COLLATE pg_catalog."default",
    oem_code character varying(10) COLLATE pg_catalog."default",
    source_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    condition_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    position_code character varying(10) COLLATE pg_catalog."default",
    finish_code character varying(10) COLLATE pg_catalog."default",
    color_code character varying(10) COLLATE pg_catalog."default",
    uom_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    barcode character varying(50) COLLATE pg_catalog."default",
    supplier_mpn character varying(50) COLLATE pg_catalog."default",
    interchange_numbers jsonb DEFAULT '[]'::jsonb,
    cross_references jsonb DEFAULT '[]'::jsonb,
    weight_kg numeric(8, 3),
    dimensions_cm character varying(50) COLLATE pg_catalog."default",
    package_qty integer DEFAULT 1,
    min_stock integer DEFAULT 0,
    max_stock integer DEFAULT 1000,
    reorder_point integer DEFAULT 0,
    safety_stock integer DEFAULT 0,
    lead_time_days integer DEFAULT 7,
    core_required boolean DEFAULT false,
    core_price numeric(10, 2) DEFAULT 0,
    warranty_days integer DEFAULT 90,
    standard_cost numeric(10, 2) DEFAULT 0,
    avg_cost numeric(10, 2) DEFAULT 0,
    last_purchase_cost numeric(10, 2) DEFAULT 0,
    is_active boolean DEFAULT true,
    is_serialized boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    notes text COLLATE pg_catalog."default",
    CONSTRAINT product_master_pkey PRIMARY KEY (internal_sku)
);

CREATE TABLE IF NOT EXISTS inv.product_prices
(
    product_price_id serial NOT NULL,
    price_list_id integer NOT NULL,
    internal_sku character varying(20) COLLATE pg_catalog."default" NOT NULL,
    unit_price numeric(10, 2) NOT NULL,
    tax_percent numeric(5, 2) DEFAULT 0,
    discount_percent numeric(5, 2) DEFAULT 0,
    min_qty integer DEFAULT 1,
    valid_from date DEFAULT CURRENT_DATE,
    valid_until date,
    CONSTRAINT product_prices_pkey PRIMARY KEY (product_price_id),
    CONSTRAINT product_prices_price_list_id_internal_sku_valid_from_key UNIQUE (price_list_id, internal_sku, valid_from)
);

CREATE TABLE IF NOT EXISTS inv.purchase_orders
(
    po_id serial NOT NULL,
    po_number character varying(30) COLLATE pg_catalog."default" NOT NULL,
    supplier_id integer NOT NULL,
    order_date date DEFAULT CURRENT_DATE,
    expected_delivery_date date,
    actual_delivery_date date,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'DRAFT'::character varying,
    subtotal numeric(12, 2) DEFAULT 0,
    tax_amount numeric(12, 2) DEFAULT 0,
    shipping_cost numeric(10, 2) DEFAULT 0,
    total_amount numeric(12, 2) GENERATED ALWAYS AS (((subtotal + tax_amount) + shipping_cost)) STORED,
    created_by integer,
    approved_by integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    notes text COLLATE pg_catalog."default",
    CONSTRAINT purchase_orders_pkey PRIMARY KEY (po_id),
    CONSTRAINT purchase_orders_po_number_key UNIQUE (po_number)
);

CREATE TABLE IF NOT EXISTS inv.stock
(
    stock_id bigserial NOT NULL,
    internal_sku character varying(20) COLLATE pg_catalog."default" NOT NULL,
    warehouse_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    bin_id integer,
    qty_on_hand integer NOT NULL DEFAULT 0,
    qty_reserved integer NOT NULL DEFAULT 0,
    qty_available integer GENERATED ALWAYS AS ((qty_on_hand - qty_reserved)) STORED,
    qty_on_order integer DEFAULT 0,
    batch_number character varying(50) COLLATE pg_catalog."default",
    serial_number character varying(100) COLLATE pg_catalog."default",
    expiration_date date,
    manufacturing_date date,
    unit_cost numeric(10, 2) DEFAULT 0,
    total_cost numeric(12, 2) GENERATED ALWAYS AS (((qty_on_hand)::numeric * unit_cost)) STORED,
    last_receipt_date date NOT NULL DEFAULT CURRENT_DATE,
    last_count_date date,
    next_count_date date,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'AVAILABLE'::character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    notes text COLLATE pg_catalog."default",
    CONSTRAINT stock_pkey PRIMARY KEY (stock_id, last_receipt_date),
    CONSTRAINT stock_internal_sku_warehouse_code_bin_id_batch_number_seria_key UNIQUE (internal_sku, warehouse_code, bin_id, batch_number, serial_number, last_receipt_date)
);

COMMENT ON TABLE inv.stock
    IS 'Existencias físicas particionadas por fecha de recepción para optimizar purga de datos históricos.';

COMMENT ON COLUMN inv.stock.qty_available
    IS 'Cálculo dinámico: Existencia física menos unidades comprometidas en WOs.';

COMMENT ON COLUMN inv.stock.last_receipt_date
    IS 'Clave de particionamiento. Determina en qué tabla física reside el registro.';

CREATE TABLE IF NOT EXISTS inv.transactions
(
    txn_id bigserial NOT NULL,
    txn_type character varying(20) COLLATE pg_catalog."default" NOT NULL,
    txn_date timestamp without time zone NOT NULL DEFAULT now(),
    internal_sku character varying(20) COLLATE pg_catalog."default" NOT NULL,
    qty integer NOT NULL,
    uom_code character varying(10) COLLATE pg_catalog."default",
    from_warehouse character varying(20) COLLATE pg_catalog."default",
    from_bin character varying(30) COLLATE pg_catalog."default",
    to_warehouse character varying(20) COLLATE pg_catalog."default",
    to_bin character varying(30) COLLATE pg_catalog."default",
    unit_cost numeric(10, 2),
    total_cost numeric(12, 2) GENERATED ALWAYS AS (((qty)::numeric * unit_cost)) STORED,
    reference_number character varying(50) COLLATE pg_catalog."default",
    reference_type character varying(20) COLLATE pg_catalog."default",
    work_order_id integer,
    purchase_order_id integer,
    sales_order_id integer,
    performed_by integer,
    approved_by integer,
    created_at timestamp without time zone DEFAULT now(),
    notes text COLLATE pg_catalog."default",
    CONSTRAINT transactions_pkey PRIMARY KEY (txn_id, txn_date)
);

CREATE TABLE IF NOT EXISTS inv.warehouses
(
    warehouse_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    type character varying(20) COLLATE pg_catalog."default",
    address text COLLATE pg_catalog."default",
    contact_phone character varying(20) COLLATE pg_catalog."default",
    manager character varying(100) COLLATE pg_catalog."default",
    capacity integer,
    current_occupancy integer DEFAULT 0,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT warehouses_pkey PRIMARY KEY (warehouse_code)
);

CREATE TABLE IF NOT EXISTS kpi.wo_metrics
(
    metric_id serial NOT NULL,
    wo_id integer NOT NULL,
    efficiency_score numeric(5, 2),
    productivity_score numeric(5, 2),
    quality_score numeric(5, 2),
    customer_satisfaction numeric(5, 2),
    lead_time_days numeric(5, 2),
    process_time_days numeric(5, 2),
    wait_time_days numeric(5, 2),
    parts_fill_rate numeric(5, 2),
    parts_accuracy numeric(5, 2),
    return_rate numeric(5, 2),
    profitability numeric(5, 2),
    labor_utilization numeric(5, 2),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT wo_metrics_pkey PRIMARY KEY (metric_id),
    CONSTRAINT wo_metrics_wo_id_key UNIQUE (wo_id)
);

CREATE TABLE IF NOT EXISTS oem.brands
(
    brand_id serial NOT NULL,
    oem_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    country character varying(50) COLLATE pg_catalog."default",
    website character varying(200) COLLATE pg_catalog."default",
    support_email character varying(100) COLLATE pg_catalog."default",
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT brands_pkey PRIMARY KEY (brand_id),
    CONSTRAINT brands_oem_code_key UNIQUE (oem_code)
);

CREATE TABLE IF NOT EXISTS oem.catalog_items
(
    catalog_id serial NOT NULL,
    oem_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    part_number character varying(30) COLLATE pg_catalog."default" NOT NULL,
    part_number_type character varying(15) COLLATE pg_catalog."default",
    description_es text COLLATE pg_catalog."default",
    description_en text COLLATE pg_catalog."default",
    group_code character varying(20) COLLATE pg_catalog."default",
    weight_kg numeric(8, 3),
    dimensions character varying(100) COLLATE pg_catalog."default",
    material character varying(50) COLLATE pg_catalog."default",
    vin_patterns text[] COLLATE pg_catalog."default",
    model_codes text[] COLLATE pg_catalog."default",
    body_codes text[] COLLATE pg_catalog."default",
    engine_codes text[] COLLATE pg_catalog."default",
    transmission_codes text[] COLLATE pg_catalog."default",
    axle_codes text[] COLLATE pg_catalog."default",
    color_codes text[] COLLATE pg_catalog."default",
    trim_codes text[] COLLATE pg_catalog."default",
    manual_types character varying(20)[] COLLATE pg_catalog."default",
    manual_refs text[] COLLATE pg_catalog."default",
    list_price numeric(10, 2),
    net_price numeric(10, 2),
    currency_code character varying(3) COLLATE pg_catalog."default" DEFAULT 'USD'::character varying,
    oem_lead_time_days integer,
    is_discontinued boolean DEFAULT false,
    valid_from date,
    valid_until date,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT catalog_items_pkey PRIMARY KEY (catalog_id),
    CONSTRAINT catalog_items_oem_code_part_number_key UNIQUE (oem_code, part_number)
);

CREATE TABLE IF NOT EXISTS oem.equivalences
(
    equivalence_id serial NOT NULL,
    oem_part_number character varying(30) COLLATE pg_catalog."default" NOT NULL,
    oem_code character varying(10) COLLATE pg_catalog."default" NOT NULL,
    aftermarket_sku character varying(20) COLLATE pg_catalog."default",
    equivalence_type character varying(20) COLLATE pg_catalog."default",
    confidence_score integer,
    notes text COLLATE pg_catalog."default",
    verified_by integer,
    verified_date date,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT equivalences_pkey PRIMARY KEY (equivalence_id),
    CONSTRAINT equivalences_oem_part_number_oem_code_aftermarket_sku_key UNIQUE (oem_part_number, oem_code, aftermarket_sku)
);

CREATE TABLE IF NOT EXISTS svc.flat_rate_standards
(
    standard_id serial NOT NULL,
    service_code character varying(20) COLLATE pg_catalog."default" NOT NULL,
    description_es text COLLATE pg_catalog."default" NOT NULL,
    description_en text COLLATE pg_catalog."default",
    equipment_type_id integer,
    group_code character varying(20) COLLATE pg_catalog."default",
    standard_hours numeric(5, 2) NOT NULL,
    min_hours numeric(5, 2),
    max_hours numeric(5, 2),
    difficulty_level integer,
    required_tools text[] COLLATE pg_catalog."default",
    required_skills text[] COLLATE pg_catalog."default",
    manual_source character varying(50) COLLATE pg_catalog."default",
    manual_ref character varying(100) COLLATE pg_catalog."default",
    oem_ref character varying(30) COLLATE pg_catalog."default",
    valid_from date DEFAULT CURRENT_DATE,
    valid_until date,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT flat_rate_standards_pkey PRIMARY KEY (standard_id),
    CONSTRAINT flat_rate_standards_service_code_key UNIQUE (service_code)
);

CREATE TABLE IF NOT EXISTS svc.invoice_items
(
    invoice_item_id serial NOT NULL,
    invoice_id integer NOT NULL,
    internal_sku character varying(20) COLLATE pg_catalog."default",
    description text COLLATE pg_catalog."default" NOT NULL,
    qty numeric(10, 3) NOT NULL,
    unit_price numeric(10, 2) NOT NULL,
    tax_percent numeric(5, 2) DEFAULT 0,
    discount_percent numeric(5, 2) DEFAULT 0,
    line_total numeric(10, 2) GENERATED ALWAYS AS ((((qty * unit_price) * ((1)::numeric + (tax_percent / (100)::numeric))) * ((1)::numeric - (discount_percent / (100)::numeric)))) STORED,
    CONSTRAINT invoice_items_pkey PRIMARY KEY (invoice_item_id)
);

CREATE TABLE IF NOT EXISTS svc.invoices
(
    invoice_id serial NOT NULL,
    invoice_number character varying(30) COLLATE pg_catalog."default" NOT NULL,
    wo_id integer,
    client_id integer NOT NULL,
    currency_code character varying(3) COLLATE pg_catalog."default",
    subtotal numeric(12, 2) DEFAULT 0,
    tax_amount numeric(12, 2) DEFAULT 0,
    discount_amount numeric(12, 2) DEFAULT 0,
    total_amount numeric(12, 2) GENERATED ALWAYS AS (((subtotal + tax_amount) - discount_amount)) STORED,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'DRAFT'::character varying,
    issue_date date DEFAULT CURRENT_DATE,
    due_date date,
    paid_date date,
    notes text COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT invoices_pkey PRIMARY KEY (invoice_id),
    CONSTRAINT invoices_invoice_number_key UNIQUE (invoice_number)
);

CREATE TABLE IF NOT EXISTS svc.payments
(
    payment_id serial NOT NULL,
    invoice_id integer NOT NULL,
    payment_date date DEFAULT CURRENT_DATE,
    amount numeric(12, 2) NOT NULL,
    currency_code character varying(3) COLLATE pg_catalog."default",
    payment_method character varying(20) COLLATE pg_catalog."default" NOT NULL,
    reference_number character varying(50) COLLATE pg_catalog."default",
    notes text COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT payments_pkey PRIMARY KEY (payment_id)
);

COMMENT ON TABLE svc.payments
    IS 'Registro de abonos y pagos aplicados a facturas de servicio.';

COMMENT ON COLUMN svc.payments.amount
    IS 'Monto del pago. Validado mediante trigger contra el total de la factura.';

COMMENT ON COLUMN svc.payments.reference_number
    IS 'Número de comprobante de transferencia, cheque o terminal bancaria.';

CREATE TABLE IF NOT EXISTS svc.service_checklists
(
    checklist_id serial NOT NULL,
    flat_rate_id integer,
    description text COLLATE pg_catalog."default" NOT NULL,
    sequence_no integer NOT NULL,
    is_critical boolean DEFAULT false,
    expected_result character varying(100) COLLATE pg_catalog."default",
    tool_required character varying(100) COLLATE pg_catalog."default",
    estimated_minutes integer,
    CONSTRAINT service_checklists_pkey PRIMARY KEY (checklist_id),
    CONSTRAINT service_checklists_flat_rate_id_sequence_no_key UNIQUE (flat_rate_id, sequence_no)
);

CREATE TABLE IF NOT EXISTS svc.wo_items
(
    item_id serial NOT NULL,
    wo_id integer NOT NULL,
    internal_sku character varying(20) COLLATE pg_catalog."default",
    qty_ordered numeric(10, 3) NOT NULL DEFAULT 1,
    qty_used numeric(10, 3) NOT NULL DEFAULT 0,
    qty_returned numeric(10, 3) DEFAULT 0,
    unit_price numeric(10, 2) NOT NULL DEFAULT 0,
    discount_percent numeric(5, 2) DEFAULT 0,
    tax_percent numeric(5, 2) DEFAULT 0,
    line_total numeric(10, 2) GENERATED ALWAYS AS ((((qty_used * unit_price) * ((1)::numeric - (discount_percent / (100)::numeric))) * ((1)::numeric + (tax_percent / (100)::numeric)))) STORED,
    reserved_stock_id bigint,
    reserved_stock_date date,
    used_stock_id bigint,
    used_stock_date date,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'PENDING'::character varying,
    notes text COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT wo_items_pkey PRIMARY KEY (item_id)
);

COMMENT ON TABLE svc.wo_items
    IS 'Detalle de repuestos e insumos utilizados en una Orden de Servicio.';

COMMENT ON COLUMN svc.wo_items.line_total
    IS 'Cálculo automático: Cantidad utilizada por precio neto tras descuentos e impuestos.';

COMMENT ON COLUMN svc.wo_items.reserved_stock_date
    IS 'Obligatorio para referenciar la partición correcta en inv.stock.';

CREATE TABLE IF NOT EXISTS svc.wo_services
(
    service_id serial NOT NULL,
    wo_id integer NOT NULL,
    flat_rate_id integer,
    service_code character varying(20) COLLATE pg_catalog."default",
    description text COLLATE pg_catalog."default" NOT NULL,
    flat_hours numeric(5, 2) DEFAULT 0,
    estimated_hours numeric(5, 2) DEFAULT 0,
    actual_hours numeric(5, 2) DEFAULT 0,
    hourly_rate numeric(10, 2) DEFAULT 0,
    labor_cost numeric(10, 2) GENERATED ALWAYS AS ((actual_hours * hourly_rate)) STORED,
    completion_status character varying(20) COLLATE pg_catalog."default" DEFAULT 'PENDING'::character varying,
    technician_id integer,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    notes text COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT wo_services_pkey PRIMARY KEY (service_id)
);

COMMENT ON TABLE svc.wo_services
    IS 'Desglose de tareas de mano de obra vinculadas a una Orden de Servicio en Forge DB.';

COMMENT ON COLUMN svc.wo_services.flat_hours
    IS 'Tiempo estándar definido por catálogo para esta tarea específica.';

COMMENT ON COLUMN svc.wo_services.labor_cost
    IS 'Cálculo automático: Horas reales trabajadas por la tarifa por hora asignada.';

CREATE TABLE IF NOT EXISTS svc.work_orders
(
    wo_id serial NOT NULL,
    wo_number character varying(30) COLLATE pg_catalog."default" NOT NULL,
    equipment_id integer NOT NULL,
    client_id integer NOT NULL,
    appointment_date timestamp without time zone,
    reception_date timestamp without time zone,
    diagnosis_date timestamp without time zone,
    estimated_start_date timestamp without time zone,
    actual_start_date timestamp without time zone,
    estimated_completion_date timestamp without time zone,
    actual_completion_date timestamp without time zone,
    qc_date timestamp without time zone,
    delivery_date timestamp without time zone,
    service_type character varying(30) COLLATE pg_catalog."default" NOT NULL,
    customer_complaints text COLLATE pg_catalog."default",
    initial_findings text COLLATE pg_catalog."default",
    technician_notes text COLLATE pg_catalog."default",
    qc_notes text COLLATE pg_catalog."default",
    final_report text COLLATE pg_catalog."default",
    flat_rate_hours numeric(5, 2) DEFAULT 0,
    estimated_hours numeric(5, 2) DEFAULT 0,
    actual_hours numeric(5, 2) DEFAULT 0,
    efficiency_rate numeric(5, 2) GENERATED ALWAYS AS (
CASE
    WHEN (actual_hours > (0)::numeric) THEN ((flat_rate_hours / actual_hours) * (100)::numeric)
    ELSE (0)::numeric
END) STORED,
    labor_rate numeric(10, 2) DEFAULT 0,
    labor_cost numeric(10, 2) GENERATED ALWAYS AS ((actual_hours * labor_rate)) STORED,
    parts_cost numeric(10, 2) DEFAULT 0,
    additional_costs numeric(10, 2) DEFAULT 0,
    total_cost numeric(12, 2) GENERATED ALWAYS AS ((((actual_hours * labor_rate) + parts_cost) + additional_costs)) STORED,
    quoted_price numeric(10, 2),
    discount_amount numeric(10, 2) DEFAULT 0,
    final_price numeric(10, 2) GENERATED ALWAYS AS ((COALESCE(quoted_price, (((actual_hours * labor_rate) + parts_cost) + additional_costs)) - discount_amount)) STORED,
    status character varying(30) COLLATE pg_catalog."default" DEFAULT 'DRAFT'::character varying,
    priority character varying(10) COLLATE pg_catalog."default" DEFAULT 'NORMAL'::character varying,
    advisor_id integer,
    technician_id integer,
    qc_technician_id integer,
    mileage_in integer,
    mileage_out integer,
    hours_in integer,
    hours_out integer,
    created_by integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    closed_at timestamp without time zone,
    notes text COLLATE pg_catalog."default",
    CONSTRAINT work_orders_pkey PRIMARY KEY (wo_id),
    CONSTRAINT work_orders_wo_number_key UNIQUE (wo_number)
);

COMMENT ON TABLE svc.work_orders
    IS 'Registro principal de órdenes de servicio. Orquesta técnicos, repuestos y costos.';

COMMENT ON COLUMN svc.work_orders.efficiency_rate
    IS 'Métrica de productividad: (Horas Estándar / Horas Reales) * 100.';

COMMENT ON COLUMN svc.work_orders.total_cost
    IS 'Suma automática de Mano de Obra (Horas x Tarifa) + Repuestos + Gastos Adicionales.';

COMMENT ON COLUMN svc.work_orders.final_price
    IS 'Monto final a cobrar tras aplicar descuentos sobre el presupuesto o el costo total.';

ALTER TABLE IF EXISTS app.alerts
    ADD CONSTRAINT alerts_assigned_to_fkey FOREIGN KEY (assigned_to)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;
CREATE INDEX IF NOT EXISTS idx_alerts_assigned
    ON app.alerts(assigned_to);


ALTER TABLE IF EXISTS app.alerts
    ADD CONSTRAINT alerts_created_for_fkey FOREIGN KEY (created_for)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS app.audit_logs
    ADD CONSTRAINT audit_logs_changed_by_fkey FOREIGN KEY (changed_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS cat.clients
    ADD CONSTRAINT clients_created_by_fkey FOREIGN KEY (created_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS cat.equipment
    ADD CONSTRAINT equipment_aspiration_code_fkey FOREIGN KEY (aspiration_code)
    REFERENCES cat.aspiration_codes (aspiration_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS cat.equipment
    ADD CONSTRAINT equipment_client_id_fkey FOREIGN KEY (client_id)
    REFERENCES cat.clients (client_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;


ALTER TABLE IF EXISTS cat.equipment
    ADD CONSTRAINT equipment_created_by_fkey FOREIGN KEY (created_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS cat.equipment
    ADD CONSTRAINT equipment_drivetrain_code_fkey FOREIGN KEY (drivetrain_code)
    REFERENCES cat.drivetrain_codes (drivetrain_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS cat.equipment
    ADD CONSTRAINT equipment_fuel_code_fkey FOREIGN KEY (fuel_code)
    REFERENCES cat.fuel_codes (fuel_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS cat.equipment
    ADD CONSTRAINT equipment_transmission_code_fkey FOREIGN KEY (transmission_code)
    REFERENCES cat.transmission_codes (transmission_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS cat.equipment
    ADD CONSTRAINT equipment_type_id_fkey FOREIGN KEY (type_id)
    REFERENCES cat.equipment_types (type_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;


ALTER TABLE IF EXISTS cat.fitment
    ADD CONSTRAINT fitment_equipment_id_fkey FOREIGN KEY (equipment_id)
    REFERENCES cat.equipment (equipment_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS cat.fitment
    ADD CONSTRAINT fitment_internal_sku_fkey FOREIGN KEY (internal_sku)
    REFERENCES inv.product_master (internal_sku) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS cat.fitment
    ADD CONSTRAINT fitment_verified_by_fkey FOREIGN KEY (verified_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS cat.taxonomy_groups
    ADD CONSTRAINT taxonomy_groups_subsystem_code_fkey FOREIGN KEY (subsystem_code)
    REFERENCES cat.taxonomy_subsystems (subsystem_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_taxonomy_groups_subsystem
    ON cat.taxonomy_groups(subsystem_code);


ALTER TABLE IF EXISTS cat.taxonomy_groups
    ADD CONSTRAINT taxonomy_groups_system_code_fkey FOREIGN KEY (system_code)
    REFERENCES cat.taxonomy_systems (system_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS cat.taxonomy_subsystems
    ADD CONSTRAINT taxonomy_subsystems_system_code_fkey FOREIGN KEY (system_code)
    REFERENCES cat.taxonomy_systems (system_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_taxonomy_subsystems_system
    ON cat.taxonomy_subsystems(system_code);


ALTER TABLE IF EXISTS doc.documents
    ADD CONSTRAINT documents_taken_by_fkey FOREIGN KEY (taken_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS doc.documents
    ADD CONSTRAINT documents_uploaded_by_fkey FOREIGN KEY (uploaded_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.bins
    ADD CONSTRAINT bins_warehouse_code_fkey FOREIGN KEY (warehouse_code)
    REFERENCES inv.warehouses (warehouse_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS inv.po_items
    ADD CONSTRAINT po_items_internal_sku_fkey FOREIGN KEY (internal_sku)
    REFERENCES inv.product_master (internal_sku) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_po_items_sku
    ON inv.po_items(internal_sku);


ALTER TABLE IF EXISTS inv.po_items
    ADD CONSTRAINT po_items_po_id_fkey FOREIGN KEY (po_id)
    REFERENCES inv.purchase_orders (po_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS inv.price_lists
    ADD CONSTRAINT price_lists_currency_code_fkey FOREIGN KEY (currency_code)
    REFERENCES cat.currencies (currency_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.product_master
    ADD CONSTRAINT product_master_color_code_fkey FOREIGN KEY (color_code)
    REFERENCES cat.color_codes (color_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.product_master
    ADD CONSTRAINT product_master_condition_code_fkey FOREIGN KEY (condition_code)
    REFERENCES cat.condition_codes (condition_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.product_master
    ADD CONSTRAINT product_master_finish_code_fkey FOREIGN KEY (finish_code)
    REFERENCES cat.finish_codes (finish_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.product_master
    ADD CONSTRAINT product_master_group_code_fkey FOREIGN KEY (group_code)
    REFERENCES cat.taxonomy_groups (group_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;
CREATE INDEX IF NOT EXISTS idx_product_group
    ON inv.product_master(group_code);


ALTER TABLE IF EXISTS inv.product_master
    ADD CONSTRAINT product_master_oem_code_fkey FOREIGN KEY (oem_code)
    REFERENCES oem.brands (oem_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.product_master
    ADD CONSTRAINT product_master_position_code_fkey FOREIGN KEY (position_code)
    REFERENCES cat.position_codes (position_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.product_master
    ADD CONSTRAINT product_master_source_code_fkey FOREIGN KEY (source_code)
    REFERENCES cat.source_codes (source_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.product_master
    ADD CONSTRAINT product_master_uom_code_fkey FOREIGN KEY (uom_code)
    REFERENCES cat.uom_codes (uom_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.product_prices
    ADD CONSTRAINT product_prices_internal_sku_fkey FOREIGN KEY (internal_sku)
    REFERENCES inv.product_master (internal_sku) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS inv.product_prices
    ADD CONSTRAINT product_prices_price_list_id_fkey FOREIGN KEY (price_list_id)
    REFERENCES inv.price_lists (price_list_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS inv.purchase_orders
    ADD CONSTRAINT purchase_orders_approved_by_fkey FOREIGN KEY (approved_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.purchase_orders
    ADD CONSTRAINT purchase_orders_created_by_fkey FOREIGN KEY (created_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.purchase_orders
    ADD CONSTRAINT purchase_orders_supplier_id_fkey FOREIGN KEY (supplier_id)
    REFERENCES cat.suppliers (supplier_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;


ALTER TABLE IF EXISTS inv.stock
    ADD CONSTRAINT stock_bin_id_fkey FOREIGN KEY (bin_id)
    REFERENCES inv.bins (bin_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_stock_bin
    ON inv.stock(bin_id);


ALTER TABLE IF EXISTS inv.stock
    ADD CONSTRAINT stock_internal_sku_fkey FOREIGN KEY (internal_sku)
    REFERENCES inv.product_master (internal_sku) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS inv.stock
    ADD CONSTRAINT stock_warehouse_code_fkey FOREIGN KEY (warehouse_code)
    REFERENCES inv.warehouses (warehouse_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS inv.transactions
    ADD CONSTRAINT transactions_approved_by_fkey FOREIGN KEY (approved_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.transactions
    ADD CONSTRAINT transactions_from_warehouse_fkey FOREIGN KEY (from_warehouse)
    REFERENCES inv.warehouses (warehouse_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.transactions
    ADD CONSTRAINT transactions_internal_sku_fkey FOREIGN KEY (internal_sku)
    REFERENCES inv.product_master (internal_sku) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.transactions
    ADD CONSTRAINT transactions_performed_by_fkey FOREIGN KEY (performed_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.transactions
    ADD CONSTRAINT transactions_purchase_order_id_fkey FOREIGN KEY (purchase_order_id)
    REFERENCES inv.purchase_orders (po_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_purchase_order
    ON inv.transactions(purchase_order_id);


ALTER TABLE IF EXISTS inv.transactions
    ADD CONSTRAINT transactions_to_warehouse_fkey FOREIGN KEY (to_warehouse)
    REFERENCES inv.warehouses (warehouse_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.transactions
    ADD CONSTRAINT transactions_uom_code_fkey FOREIGN KEY (uom_code)
    REFERENCES cat.uom_codes (uom_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS inv.transactions
    ADD CONSTRAINT transactions_work_order_id_fkey FOREIGN KEY (work_order_id)
    REFERENCES svc.work_orders (wo_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_transactions_work_order
    ON inv.transactions(work_order_id);


ALTER TABLE IF EXISTS kpi.wo_metrics
    ADD CONSTRAINT wo_metrics_wo_id_fkey FOREIGN KEY (wo_id)
    REFERENCES svc.work_orders (wo_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS wo_metrics_wo_id_key
    ON kpi.wo_metrics(wo_id);


ALTER TABLE IF EXISTS oem.catalog_items
    ADD CONSTRAINT catalog_items_group_code_fkey FOREIGN KEY (group_code)
    REFERENCES cat.taxonomy_groups (group_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;
CREATE INDEX IF NOT EXISTS idx_catalog_items_group
    ON oem.catalog_items(group_code);


ALTER TABLE IF EXISTS oem.catalog_items
    ADD CONSTRAINT catalog_items_oem_code_fkey FOREIGN KEY (oem_code)
    REFERENCES oem.brands (oem_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS oem.equivalences
    ADD CONSTRAINT equivalences_aftermarket_sku_fkey FOREIGN KEY (aftermarket_sku)
    REFERENCES inv.product_master (internal_sku) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;
CREATE INDEX IF NOT EXISTS idx_equivalences_sku
    ON oem.equivalences(aftermarket_sku);


ALTER TABLE IF EXISTS oem.equivalences
    ADD CONSTRAINT equivalences_verified_by_fkey FOREIGN KEY (verified_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.flat_rate_standards
    ADD CONSTRAINT flat_rate_standards_equipment_type_id_fkey FOREIGN KEY (equipment_type_id)
    REFERENCES cat.equipment_types (type_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.flat_rate_standards
    ADD CONSTRAINT flat_rate_standards_group_code_fkey FOREIGN KEY (group_code)
    REFERENCES cat.taxonomy_groups (group_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.invoice_items
    ADD CONSTRAINT invoice_items_internal_sku_fkey FOREIGN KEY (internal_sku)
    REFERENCES inv.product_master (internal_sku) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;
CREATE INDEX IF NOT EXISTS idx_invoice_items_sku
    ON svc.invoice_items(internal_sku);


ALTER TABLE IF EXISTS svc.invoice_items
    ADD CONSTRAINT invoice_items_invoice_id_fkey FOREIGN KEY (invoice_id)
    REFERENCES svc.invoices (invoice_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice
    ON svc.invoice_items(invoice_id);


ALTER TABLE IF EXISTS svc.invoices
    ADD CONSTRAINT invoices_client_id_fkey FOREIGN KEY (client_id)
    REFERENCES cat.clients (client_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE RESTRICT;


ALTER TABLE IF EXISTS svc.invoices
    ADD CONSTRAINT invoices_currency_code_fkey FOREIGN KEY (currency_code)
    REFERENCES cat.currencies (currency_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.invoices
    ADD CONSTRAINT invoices_wo_id_fkey FOREIGN KEY (wo_id)
    REFERENCES svc.work_orders (wo_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_invoices_wo
    ON svc.invoices(wo_id);


ALTER TABLE IF EXISTS svc.payments
    ADD CONSTRAINT payments_currency_code_fkey FOREIGN KEY (currency_code)
    REFERENCES cat.currencies (currency_code) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.payments
    ADD CONSTRAINT payments_invoice_id_fkey FOREIGN KEY (invoice_id)
    REFERENCES svc.invoices (invoice_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;


ALTER TABLE IF EXISTS svc.service_checklists
    ADD CONSTRAINT service_checklists_flat_rate_id_fkey FOREIGN KEY (flat_rate_id)
    REFERENCES svc.flat_rate_standards (standard_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_service_checklists_flat
    ON svc.service_checklists(flat_rate_id);


ALTER TABLE IF EXISTS svc.wo_items
    ADD CONSTRAINT wo_items_internal_sku_fkey FOREIGN KEY (internal_sku)
    REFERENCES inv.product_master (internal_sku) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_wo_items_sku
    ON svc.wo_items(internal_sku);


ALTER TABLE IF EXISTS svc.wo_items
    ADD CONSTRAINT wo_items_reserved_stock_id_reserved_stock_date_fkey FOREIGN KEY (reserved_stock_id, reserved_stock_date)
    REFERENCES inv.stock (stock_id, last_receipt_date) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.wo_items
    ADD CONSTRAINT wo_items_used_stock_id_used_stock_date_fkey FOREIGN KEY (used_stock_id, used_stock_date)
    REFERENCES inv.stock (stock_id, last_receipt_date) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.wo_items
    ADD CONSTRAINT wo_items_wo_id_fkey FOREIGN KEY (wo_id)
    REFERENCES svc.work_orders (wo_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_wo_items_wo
    ON svc.wo_items(wo_id);


ALTER TABLE IF EXISTS svc.wo_services
    ADD CONSTRAINT wo_services_flat_rate_id_fkey FOREIGN KEY (flat_rate_id)
    REFERENCES svc.flat_rate_standards (standard_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.wo_services
    ADD CONSTRAINT wo_services_technician_id_fkey FOREIGN KEY (technician_id)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.wo_services
    ADD CONSTRAINT wo_services_wo_id_fkey FOREIGN KEY (wo_id)
    REFERENCES svc.work_orders (wo_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_wo_services_wo
    ON svc.wo_services(wo_id);


ALTER TABLE IF EXISTS svc.work_orders
    ADD CONSTRAINT work_orders_advisor_id_fkey FOREIGN KEY (advisor_id)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.work_orders
    ADD CONSTRAINT work_orders_client_id_fkey FOREIGN KEY (client_id)
    REFERENCES cat.clients (client_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;


ALTER TABLE IF EXISTS svc.work_orders
    ADD CONSTRAINT work_orders_created_by_fkey FOREIGN KEY (created_by)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.work_orders
    ADD CONSTRAINT work_orders_equipment_id_fkey FOREIGN KEY (equipment_id)
    REFERENCES cat.equipment (equipment_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE SET NULL;


ALTER TABLE IF EXISTS svc.work_orders
    ADD CONSTRAINT work_orders_qc_technician_id_fkey FOREIGN KEY (qc_technician_id)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;


ALTER TABLE IF EXISTS svc.work_orders
    ADD CONSTRAINT work_orders_technician_id_fkey FOREIGN KEY (technician_id)
    REFERENCES cat.technicians (technician_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

END;