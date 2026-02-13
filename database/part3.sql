-- =====================================================
-- PARTE 3: FUNCIONES Y STORED PROCEDURES - LO MEJOR DE AMBAS VERSIONES
-- =====================================================

-- =====================================================
-- 1. FUNCIONES DE INVENTARIO
-- =====================================================

-- Función para obtener stock disponible por producto (mejorada)
CREATE OR REPLACE FUNCTION inv.get_available_stock(
    p_sku VARCHAR DEFAULT NULL,
    p_warehouse_code VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    internal_sku VARCHAR,
    product_name VARCHAR,
    warehouse_code VARCHAR,
    warehouse_name VARCHAR,
    bin_code VARCHAR,
    qty_available INTEGER,
    qty_reserved INTEGER,
    qty_on_hand INTEGER,
    unit_cost DECIMAL,
    total_cost DECIMAL,
    reorder_point INTEGER,
    min_stock INTEGER,
    last_receipt_date DATE,
    status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.internal_sku,
        pm.name as product_name,
        s.warehouse_code,
        wh.name as warehouse_name,
        b.bin_code,
        s.qty_available,
        s.qty_reserved,
        s.qty_on_hand,
        s.unit_cost,
        s.total_cost,
        pm.reorder_point,
        pm.min_stock,
        s.last_receipt_date,
        s.status
    FROM inv.stock s
    JOIN inv.product_master pm ON s.internal_sku = pm.internal_sku
    JOIN inv.warehouses wh ON s.warehouse_code = wh.warehouse_code
    LEFT JOIN inv.bins b ON s.bin_id = b.bin_id
    WHERE s.qty_available > 0
    AND s.status = 'AVAILABLE'
    AND pm.is_active = TRUE
    AND (p_sku IS NULL OR s.internal_sku = p_sku)
    AND (p_warehouse_code IS NULL OR s.warehouse_code = p_warehouse_code)
    ORDER BY 
        CASE 
            WHEN s.qty_available < pm.reorder_point THEN 1
            WHEN s.qty_available < pm.min_stock THEN 2
            ELSE 3
        END,
        s.unit_cost ASC,
        s.qty_available DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para calcular edad del inventario (mejorada)
CREATE OR REPLACE FUNCTION inv.calculate_inventory_age(
    p_days_threshold INTEGER DEFAULT 90
)
RETURNS TABLE (
    internal_sku VARCHAR,
    product_name VARCHAR,
    group_name VARCHAR,
    warehouse_code VARCHAR,
    bin_code VARCHAR,
    days_in_stock INTEGER,
    qty_on_hand INTEGER,
    unit_cost DECIMAL,
    total_value DECIMAL,
    aging_category VARCHAR,
    last_movement_date DATE,
    turnover_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH movement_stats AS (
        SELECT 
            t.internal_sku,
            MAX(t.txn_date) as last_movement_date,
            COUNT(DISTINCT CASE WHEN t.txn_type = 'OUT' THEN t.txn_id END) as out_count,
            SUM(CASE WHEN t.txn_type = 'OUT' THEN ABS(t.qty) ELSE 0 END) as out_qty
        FROM inv.transactions t
        WHERE t.txn_date >= CURRENT_DATE - INTERVAL '1 year'
        GROUP BY t.internal_sku
    )
    SELECT 
        s.internal_sku,
        pm.name as product_name,
        tg.name_es as group_name,
        s.warehouse_code,
        b.bin_code,
        CURRENT_DATE - s.last_receipt_date as days_in_stock,
        s.qty_on_hand,
        s.unit_cost,
        s.total_cost,
        CASE 
            WHEN CURRENT_DATE - s.last_receipt_date > 365 THEN 'OBSOLETO (>1 año)'
            WHEN CURRENT_DATE - s.last_receipt_date > 180 THEN 'MUY LENTO (6-12 meses)'
            WHEN CURRENT_DATE - s.last_receipt_date > 90 THEN 'LENTO (3-6 meses)'
            WHEN CURRENT_DATE - s.last_receipt_date > 30 THEN 'NORMAL (1-3 meses)'
            ELSE 'FRESCO (<1 mes)'
        END as aging_category,
        ms.last_movement_date,
        CASE 
            WHEN s.qty_on_hand > 0 
            THEN ROUND(COALESCE(ms.out_qty, 0)::DECIMAL / s.qty_on_hand * 12, 2)
            ELSE 0 
        END as turnover_rate
    FROM inv.stock s
    JOIN inv.product_master pm ON s.internal_sku = pm.internal_sku
    LEFT JOIN inv.bins b ON s.bin_id = b.bin_id
    LEFT JOIN cat.taxonomy_groups tg ON pm.group_code = tg.group_code
    LEFT JOIN movement_stats ms ON s.internal_sku = ms.internal_sku
    WHERE s.qty_on_hand > 0
    AND pm.is_active = TRUE
    ORDER BY days_in_stock DESC, total_value DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para crear transacción de inventario (robusta)
CREATE OR REPLACE FUNCTION inv.create_transaction(
    p_txn_type VARCHAR,
    p_internal_sku VARCHAR,
    p_qty INTEGER,
    p_from_warehouse VARCHAR DEFAULT NULL,
    p_from_bin VARCHAR DEFAULT NULL,
    p_to_warehouse VARCHAR DEFAULT NULL,
    p_to_bin VARCHAR DEFAULT NULL,
    p_unit_cost DECIMAL DEFAULT NULL,
    p_reference_number VARCHAR DEFAULT NULL,
    p_reference_type VARCHAR DEFAULT NULL,
    p_work_order_id INTEGER DEFAULT NULL,
    p_purchase_order_id INTEGER DEFAULT NULL,
    p_performed_by INTEGER DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_txn_id BIGINT;
    v_current_stock INTEGER;
    v_available_stock INTEGER;
    v_product RECORD;
    v_result JSONB;
BEGIN
    -- Validar tipo de transacción
    IF p_txn_type NOT IN ('IN', 'OUT', 'TRANSFER', 'ADJUST', 'RESERVE', 'RELEASE', 'COUNT') THEN
        RAISE EXCEPTION 'Tipo de transacción inválido: %', p_txn_type;
    END IF;

    -- Validar producto
    SELECT * INTO v_product FROM inv.product_master WHERE internal_sku = p_internal_sku;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Producto no encontrado: %', p_internal_sku;
    END IF;

    -- Validar cantidades para transacciones OUT
    IF p_txn_type IN ('OUT', 'TRANSFER') AND p_from_warehouse IS NOT NULL THEN
        SELECT COALESCE(SUM(qty_available), 0) INTO v_available_stock
        FROM inv.stock
        WHERE internal_sku = p_internal_sku AND warehouse_code = p_from_warehouse;
        
        IF v_available_stock < p_qty THEN
            RAISE EXCEPTION 'Stock insuficiente. Disponible: %, Solicitado: %', v_available_stock, p_qty;
        END IF;
    END IF;

    -- Validar warehouses para TRANSFER
    IF p_txn_type = 'TRANSFER' AND (p_from_warehouse IS NULL OR p_to_warehouse IS NULL) THEN
        RAISE EXCEPTION 'Transferencia requiere warehouse de origen y destino';
    END IF;

    IF p_txn_type = 'TRANSFER' AND p_from_warehouse = p_to_warehouse THEN
        RAISE EXCEPTION 'No se puede transferir al mismo warehouse';
    END IF;

    -- Insertar transacción
    INSERT INTO inv.transactions (
        txn_type,
        internal_sku,
        qty,
        from_warehouse,
        from_bin,
        to_warehouse,
        to_bin,
        unit_cost,
        reference_number,
        reference_type,
        work_order_id,
        purchase_order_id,
        performed_by,
        notes
    ) VALUES (
        p_txn_type,
        p_internal_sku,
        p_qty,
        p_from_warehouse,
        p_from_bin,
        p_to_warehouse,
        p_to_bin,
        p_unit_cost,
        p_reference_number,
        p_reference_type,
        p_work_order_id,
        p_purchase_order_id,
        p_performed_by,
        p_notes
    ) RETURNING txn_id INTO v_txn_id;

    -- Actualizar costos promedio si es entrada
    IF p_txn_type = 'IN' AND p_unit_cost IS NOT NULL THEN
        UPDATE inv.product_master 
        SET avg_cost = (
            (avg_cost * COALESCE((SELECT SUM(qty_on_hand) FROM inv.stock WHERE internal_sku = p_internal_sku), 0) + 
             p_unit_cost * p_qty) / 
            (COALESCE((SELECT SUM(qty_on_hand) FROM inv.stock WHERE internal_sku = p_internal_sku), 0) + p_qty)
        ),
        last_purchase_cost = p_unit_cost,
        updated_at = NOW()
        WHERE internal_sku = p_internal_sku;
    END IF;

    -- Retornar resultado
    v_result := jsonb_build_object(
        'success', true,
        'transaction_id', v_txn_id,
        'message', 'Transacción creada exitosamente',
        'timestamp', NOW()
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'transaction_id', NULL,
            'timestamp', NOW()
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para reservar stock para una OT
CREATE OR REPLACE FUNCTION inv.reserve_stock_for_wo(
    p_wo_id INTEGER,
    p_internal_sku VARCHAR,
    p_qty_needed DECIMAL,
    p_warehouse_code VARCHAR DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_stock_id BIGINT;
    v_available_qty INTEGER;
    v_wo_status VARCHAR;
    v_product RECORD;
    v_result JSONB;
BEGIN
    -- Validar OT
    SELECT status INTO v_wo_status FROM svc.work_orders WHERE wo_id = p_wo_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Orden de trabajo no encontrada: %', p_wo_id;
    END IF;

    IF v_wo_status IN ('CERRADO', 'CANCELLED') THEN
        RAISE EXCEPTION 'No se puede reservar stock para OT en estado: %', v_wo_status;
    END IF;

    -- Validar producto
    SELECT * INTO v_product FROM inv.product_master WHERE internal_sku = p_internal_sku;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Producto no encontrado: %', p_internal_sku;
    END IF;

    -- Encontrar stock disponible
    SELECT stock_id, qty_available INTO v_stock_id, v_available_qty
    FROM inv.stock
    WHERE internal_sku = p_internal_sku
    AND qty_available >= CEIL(p_qty_needed)
    AND status = 'AVAILABLE'
    AND (p_warehouse_code IS NULL OR warehouse_code = p_warehouse_code)
    ORDER BY unit_cost ASC, last_receipt_date ASC
    LIMIT 1;

    IF v_stock_id IS NULL THEN
        RETURN jsonb_build_object(
            'success', false,
            'message', 'Stock insuficiente para reservar',
            'available_qty', COALESCE(v_available_qty, 0),
            'needed_qty', p_qty_needed
        );
    END IF;

    -- Actualizar stock a RESERVED
    UPDATE inv.stock 
    SET qty_reserved = qty_reserved + CEIL(p_qty_needed),
        status = CASE 
            WHEN qty_available - CEIL(p_qty_needed) <= 0 THEN 'RESERVED'
            ELSE 'AVAILABLE'
        END,
        updated_at = NOW()
    WHERE stock_id = v_stock_id;

    -- Crear o actualizar item de OT
    INSERT INTO svc.wo_items (
        wo_id,
        internal_sku,
        qty_ordered,
        qty_used,
        unit_price,
        reserved_stock_id,
        status,
        created_at
    )
    VALUES (
        p_wo_id,
        p_internal_sku,
        p_qty_needed,
        0,
        (SELECT unit_cost FROM inv.stock WHERE stock_id = v_stock_id),
        v_stock_id,
        'RESERVED',
        NOW()
    )
    ON CONFLICT (wo_id, internal_sku) DO UPDATE
    SET qty_ordered = svc.wo_items.qty_ordered + p_qty_needed,
        reserved_stock_id = v_stock_id,
        status = 'RESERVED',
        updated_at = NOW();

    -- Crear transacción de reserva
    PERFORM inv.create_transaction(
        'RESERVE',
        p_internal_sku,
        CEIL(p_qty_needed),
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        'WORK_ORDER',
        p_wo_id,
        NULL,
        NULL,
        'Reserva automática para OT ' || p_wo_id
    );

    v_result := jsonb_build_object(
        'success', true,
        'stock_id', v_stock_id,
        'reserved_qty', CEIL(p_qty_needed),
        'wo_item_id', (SELECT item_id FROM svc.wo_items WHERE wo_id = p_wo_id AND internal_sku = p_internal_sku),
        'message', 'Stock reservado exitosamente'
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al reservar stock'
        );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para liberar stock reservado
CREATE OR REPLACE FUNCTION inv.release_reserved_stock(
    p_wo_item_id INTEGER,
    p_qty_to_release DECIMAL DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_wo_item RECORD;
    v_qty_to_release DECIMAL;
BEGIN
    -- Obtener información del item
    SELECT wi.*, wo.status as wo_status 
    INTO v_wo_item
    FROM svc.wo_items wi
    JOIN svc.work_orders wo ON wi.wo_id = wo.wo_id
    WHERE wi.item_id = p_wo_item_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Item de OT no encontrado: %', p_wo_item_id;
    END IF;

    -- Determinar cantidad a liberar
    IF p_qty_to_release IS NULL THEN
        v_qty_to_release := v_wo_item.qty_ordered - v_wo_item.qty_used;
    ELSE
        v_qty_to_release := LEAST(p_qty_to_release, v_wo_item.qty_ordered - v_wo_item.qty_used);
    END IF;

    IF v_qty_to_release <= 0 THEN
        RETURN jsonb_build_object(
            'success', false,
            'message', 'No hay stock para liberar'
        );
    END IF;

    -- Liberar stock
    UPDATE inv.stock 
    SET qty_reserved = qty_reserved - CEIL(v_qty_to_release),
        status = CASE 
            WHEN qty_reserved - CEIL(v_qty_to_release) <= 0 AND qty_on_hand > 0 THEN 'AVAILABLE'
            ELSE status
        END,
        updated_at = NOW()
    WHERE stock_id = v_wo_item.reserved_stock_id;

    -- Actualizar item de OT
    UPDATE svc.wo_items 
    SET qty_ordered = qty_ordered - v_qty_to_release,
        status = CASE 
            WHEN qty_ordered - v_qty_to_release <= 0 THEN 'CANCELLED'
            ELSE 'PENDING'
        END,
        updated_at = NOW()
    WHERE item_id = p_wo_item_id;

    -- Crear transacción de liberación
    PERFORM inv.create_transaction(
        'RELEASE',
        v_wo_item.internal_sku,
        CEIL(v_qty_to_release),
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        NULL,
        'WORK_ORDER',
        v_wo_item.wo_id,
        NULL,
        NULL,
        'Liberación de reserva para OT ' || v_wo_item.wo_id
    );

    RETURN jsonb_build_object(
        'success', true,
        'released_qty', v_qty_to_release,
        'message', 'Stock liberado exitosamente'
    );

EXCEPTION
    WHEN OTHERS THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al liberar stock'
        );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 2. FUNCIONES DE ÓRDENES DE TRABAJO
-- =====================================================

-- Función para crear una nueva orden de trabajo
CREATE OR REPLACE FUNCTION svc.create_work_order(
    p_equipment_id INTEGER,
    p_client_id INTEGER,
    p_service_type VARCHAR,
    p_customer_complaints TEXT DEFAULT NULL,
    p_priority VARCHAR DEFAULT 'NORMAL',
    p_advisor_id INTEGER DEFAULT NULL,
    p_estimated_hours DECIMAL DEFAULT NULL,
    p_appointment_date TIMESTAMP DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_wo_id INTEGER;
    v_wo_number VARCHAR;
    v_equipment RECORD;
    v_client RECORD;
    v_result JSONB;
BEGIN
    -- Validar equipo
    SELECT * INTO v_equipment FROM cat.equipment WHERE equipment_id = p_equipment_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Equipo no encontrado: %', p_equipment_id;
    END IF;

    -- Validar cliente
    SELECT * INTO v_client FROM cat.clients WHERE client_id = p_client_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Cliente no encontrado: %', p_client_id;
    END IF;

    -- Validar tipo de servicio
    IF p_service_type NOT IN ('PREVENTIVO','CORRECTIVO','DIAGNÓSTICO','GARANTÍA','INSPECCIÓN') THEN
        RAISE EXCEPTION 'Tipo de servicio inválido: %', p_service_type;
    END IF;

    -- Validar prioridad
    IF p_priority NOT IN ('URGENTE','ALTA','NORMAL','BAJA') THEN
        RAISE EXCEPTION 'Prioridad inválida: %', p_priority;
    END IF;

    -- Crear orden de trabajo (el trigger generará el número)
    INSERT INTO svc.work_orders (
        equipment_id,
        client_id,
        service_type,
        customer_complaints,
        priority,
        advisor_id,
        estimated_hours,
        appointment_date,
        status,
        created_at,
        updated_at
    ) VALUES (
        p_equipment_id,
        p_client_id,
        p_service_type,
        p_customer_complaints,
        p_priority,
        p_advisor_id,
        p_estimated_hours,
        p_appointment_date,
        CASE 
            WHEN p_appointment_date IS NOT NULL THEN 'CITA'
            ELSE 'DRAFT'
        END,
        NOW(),
        NOW()
    ) RETURNING wo_id, wo_number INTO v_wo_id, v_wo_number;

    -- Actualizar equipo
    UPDATE cat.equipment 
    SET status = 'REPARACIÓN',
        updated_at = NOW()
    WHERE equipment_id = p_equipment_id;

    -- Crear documento inicial de recepción
    INSERT INTO doc.documents (
        entity_type,
        entity_id,
        doc_type,
        file_name,
        title,
        description,
        created_at
    ) VALUES (
        'WORK_ORDER',
        v_wo_id,
        'RECEPCIÓN',
        'recepcion_' || v_wo_number || '.txt',
        'Recepción de Equipo',
        'Documento inicial de recepción para OT ' || v_wo_number,
        NOW()
    );

    v_result := jsonb_build_object(
        'success', true,
        'wo_id', v_wo_id,
        'wo_number', v_wo_number,
        'message', 'Orden de trabajo creada exitosamente',
        'next_steps', ARRAY['Asignar técnico', 'Realizar diagnóstico']
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al crear orden de trabajo'
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para avanzar el estado de una OT
CREATE OR REPLACE FUNCTION svc.advance_work_order_status(
    p_wo_id INTEGER,
    p_new_status VARCHAR,
    p_technician_id INTEGER DEFAULT NULL,
    p_notes TEXT DEFAULT NULL,
    p_mileage_in INTEGER DEFAULT NULL,
    p_hours_in INTEGER DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_current_status VARCHAR;
    v_valid_transitions JSONB;
    v_equipment_id INTEGER;
    v_technician_name VARCHAR;
    v_result JSONB;
BEGIN
    -- Obtener estado actual y equipo
    SELECT status, equipment_id, technician_id 
    INTO v_current_status, v_equipment_id, p_technician_id
    FROM svc.work_orders 
    WHERE wo_id = p_wo_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Orden de trabajo no encontrada: %', p_wo_id;
    END IF;

    -- Definir transiciones válidas
    v_valid_transitions := '{
        "DRAFT": ["QUOTED", "APPROVED", "CITA"],
        "QUOTED": ["APPROVED", "CANCELLED"],
        "APPROVED": ["CITA", "CANCELLED"],
        "CITA": ["RECEPCIÓN", "CANCELLED"],
        "RECEPCIÓN": ["DIAGNÓSTICO"],
        "DIAGNÓSTICO": ["ESPERA_REPUESTOS", "EN_PROCESO", "CANCELLED"],
        "ESPERA_REPUESTOS": ["EN_PROCESO", "CANCELLED"],
        "EN_PROCESO": ["QA", "CANCELLED"],
        "QA": ["FACTURACIÓN", "EN_PROCESO"],
        "FACTURACIÓN": ["ENTREGADO"],
        "ENTREGADO": ["CERRADO"],
        "CANCELLED": []
    }'::jsonb;

    -- Validar transición
    IF NOT (v_valid_transitions -> v_current_status ? p_new_status) THEN
        RAISE EXCEPTION 'Transición inválida: % -> %', v_current_status, p_new_status;
    END IF;

    -- Validar técnico si se mueve a EN_PROCESO
    IF p_new_status = 'EN_PROCESO' AND p_technician_id IS NULL THEN
        RAISE EXCEPTION 'Se requiere técnico para iniciar trabajo';
    END IF;

    -- Obtener nombre del técnico
    IF p_technician_id IS NOT NULL THEN
        SELECT first_name || ' ' || last_name INTO v_technician_name
        FROM cat.technicians WHERE technician_id = p_technician_id;
    END IF;

    -- Actualizar estado con lógica específica por estado
    CASE p_new_status
        WHEN 'RECEPCIÓN' THEN
            UPDATE svc.work_orders 
            SET status = p_new_status,
                reception_date = NOW(),
                mileage_in = p_mileage_in,
                hours_in = p_hours_in,
                notes = COALESCE(notes || E'\n', '') || p_notes,
                updated_at = NOW()
            WHERE wo_id = p_wo_id;

        WHEN 'DIAGNÓSTICO' THEN
            UPDATE svc.work_orders 
            SET status = p_new_status,
                diagnosis_date = NOW(),
                notes = COALESCE(notes || E'\n', '') || p_notes,
                updated_at = NOW()
            WHERE wo_id = p_wo_id;

        WHEN 'EN_PROCESO' THEN
            UPDATE svc.work_orders 
            SET status = p_new_status,
                technician_id = p_technician_id,
                actual_start_date = NOW(),
                notes = COALESCE(notes || E'\n', '') || p_notes,
                updated_at = NOW()
            WHERE wo_id = p_wo_id;

            -- Crear documento de inicio de trabajo
            INSERT INTO doc.documents (
                entity_type,
                entity_id,
                doc_type,
                file_name,
                title,
                description,
                created_at
            ) VALUES (
                'WORK_ORDER',
                p_wo_id,
                'PROCESO',
                'inicio_trabajo_' || (SELECT wo_number FROM svc.work_orders WHERE wo_id = p_wo_id) || '.txt',
                'Inicio de Trabajo',
                'Inicio de trabajo por ' || v_technician_name,
                NOW()
            );

        WHEN 'QA' THEN
            UPDATE svc.work_orders 
            SET status = p_new_status,
                actual_completion_date = NOW(),
                qc_date = NOW(),
                notes = COALESCE(notes || E'\n', '') || p_notes,
                updated_at = NOW()
            WHERE wo_id = p_wo_id;

        WHEN 'ENTREGADO' THEN
            UPDATE svc.work_orders 
            SET status = p_new_status,
                delivery_date = NOW(),
                notes = COALESCE(notes || E'\n', '') || p_notes,
                updated_at = NOW()
            WHERE wo_id = p_wo_id;

            -- Actualizar equipo
            UPDATE cat.equipment 
            SET status = 'ACTIVO',
                last_service_date = NOW(),
                next_service_date = CURRENT_DATE + INTERVAL '90 days',
                current_mileage_hours = p_mileage_in,
                total_service_hours = total_service_hours + COALESCE(
                    (SELECT actual_hours FROM svc.work_orders WHERE wo_id = p_wo_id), 0
                ),
                total_service_cost = total_service_cost + COALESCE(
                    (SELECT total_cost FROM svc.work_orders WHERE wo_id = p_wo_id), 0
                ),
                updated_at = NOW()
            WHERE equipment_id = v_equipment_id;

        WHEN 'CERRADO' THEN
            UPDATE svc.work_orders 
            SET status = p_new_status,
                closed_at = NOW(),
                notes = COALESCE(notes || E'\n', '') || p_notes,
                updated_at = NOW()
            WHERE wo_id = p_wo_id;

        ELSE
            UPDATE svc.work_orders 
            SET status = p_new_status,
                notes = COALESCE(notes || E'\n', '') || p_notes,
                updated_at = NOW()
            WHERE wo_id = p_wo_id;
    END CASE;

    -- Registrar en auditoría
    INSERT INTO app.audit_logs (
        table_name,
        record_id,
        action,
        old_values,
        new_values,
        changed_at
    ) VALUES (
        'work_orders',
        p_wo_id,
        'UPDATE',
        jsonb_build_object('status', v_current_status),
        jsonb_build_object('status', p_new_status),
        NOW()
    );

    v_result := jsonb_build_object(
        'success', true,
        'wo_id', p_wo_id,
        'old_status', v_current_status,
        'new_status', p_new_status,
        'message', 'Estado actualizado exitosamente',
        'timestamp', NOW()
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al actualizar estado'
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para agregar servicio a OT
CREATE OR REPLACE FUNCTION svc.add_service_to_wo(
    p_wo_id INTEGER,
    p_service_code VARCHAR DEFAULT NULL,
    p_description TEXT,
    p_flat_hours DECIMAL DEFAULT NULL,
    p_estimated_hours DECIMAL DEFAULT NULL,
    p_hourly_rate DECIMAL DEFAULT NULL,
    p_technician_id INTEGER DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_wo_status VARCHAR;
    v_flat_rate RECORD;
    v_service_id INTEGER;
    v_result JSONB;
BEGIN
    -- Validar OT
    SELECT status INTO v_wo_status FROM svc.work_orders WHERE wo_id = p_wo_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Orden de trabajo no encontrada: %', p_wo_id;
    END IF;

    IF v_wo_status IN ('CERRADO', 'CANCELLED') THEN
        RAISE EXCEPTION 'No se pueden agregar servicios a OT en estado: %', v_wo_status;
    END IF;

    -- Buscar tarifa plana si se proporciona código
    IF p_service_code IS NOT NULL THEN
        SELECT * INTO v_flat_rate 
        FROM svc.flat_rate_standards 
        WHERE service_code = p_service_code 
        AND is_active = TRUE
        AND (valid_until IS NULL OR valid_until >= CURRENT_DATE);

        IF FOUND THEN
            -- Usar valores de tarifa plana si no se especifican
            p_description := COALESCE(p_description, v_flat_rate.description_es);
            p_flat_hours := COALESCE(p_flat_hours, v_flat_rate.standard_hours);
            p_estimated_hours := COALESCE(p_estimated_hours, v_flat_rate.standard_hours);
        END IF;
    END IF;

    -- Validar horas
    IF p_flat_hours IS NOT NULL AND p_flat_hours < 0 THEN
        RAISE EXCEPTION 'Horas planas no pueden ser negativas: %', p_flat_hours;
    END IF;

    IF p_estimated_hours IS NOT NULL AND p_estimated_hours < 0 THEN
        RAISE EXCEPTION 'Horas estimadas no pueden ser negativas: %', p_estimated_hours;
    END IF;

    -- Insertar servicio
    INSERT INTO svc.wo_services (
        wo_id,
        flat_rate_id,
        service_code,
        description,
        flat_hours,
        estimated_hours,
        hourly_rate,
        technician_id,
        created_at
    ) VALUES (
        p_wo_id,
        COALESCE(v_flat_rate.standard_id, NULL),
        p_service_code,
        p_description,
        p_flat_hours,
        p_estimated_hours,
        p_hourly_rate,
        p_technician_id,
        NOW()
    ) RETURNING service_id INTO v_service_id;

    -- Actualizar horas totales en OT si es necesario
    IF p_flat_hours IS NOT NULL THEN
        UPDATE svc.work_orders 
        SET flat_rate_hours = COALESCE(flat_rate_hours, 0) + p_flat_hours,
            estimated_hours = COALESCE(estimated_hours, 0) + COALESCE(p_estimated_hours, p_flat_hours),
            updated_at = NOW()
        WHERE wo_id = p_wo_id;
    END IF;

    v_result := jsonb_build_object(
        'success', true,
        'service_id', v_service_id,
        'message', 'Servicio agregado exitosamente',
        'flat_hours', p_flat_hours,
        'estimated_hours', p_estimated_hours
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al agregar servicio'
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para completar un servicio en OT
CREATE OR REPLACE FUNCTION svc.complete_service(
    p_service_id INTEGER,
    p_actual_hours DECIMAL,
    p_completion_status VARCHAR DEFAULT 'COMPLETED',
    p_notes TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_service RECORD;
    v_wo_status VARCHAR;
    v_result JSONB;
BEGIN
    -- Obtener información del servicio
    SELECT ws.*, wo.status as wo_status
    INTO v_service
    FROM svc.wo_services ws
    JOIN svc.work_orders wo ON ws.wo_id = wo.wo_id
    WHERE ws.service_id = p_service_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Servicio no encontrado: %', p_service_id;
    END IF;

    -- Validar estado de OT
    IF v_service.wo_status IN ('CERRADO', 'CANCELLED') THEN
        RAISE EXCEPTION 'No se puede completar servicio en OT en estado: %', v_service.wo_status;
    END IF;

    -- Validar estado de completado
    IF p_completion_status NOT IN ('COMPLETED', 'QA_PASSED', 'QA_FAILED') THEN
        RAISE EXCEPTION 'Estado de completado inválido: %', p_completion_status;
    END IF;

    -- Validar horas reales
    IF p_actual_hours < 0 THEN
        RAISE EXCEPTION 'Horas reales no pueden ser negativas: %', p_actual_hours;
    END IF;

    -- Actualizar servicio
    UPDATE svc.wo_services 
    SET actual_hours = p_actual_hours,
        completion_status = p_completion_status,
        completed_at = CASE 
            WHEN completed_at IS NULL AND p_completion_status IN ('COMPLETED', 'QA_PASSED', 'QA_FAILED') 
            THEN NOW() 
            ELSE completed_at 
        END,
        notes = COALESCE(notes || E'\n', '') || p_notes,
        updated_at = NOW()
    WHERE service_id = p_service_id;

    -- Actualizar horas reales totales en OT
    UPDATE svc.work_orders 
    SET actual_hours = COALESCE(actual_hours, 0) + p_actual_hours,
        updated_at = NOW()
    WHERE wo_id = v_service.wo_id;

    v_result := jsonb_build_object(
        'success', true,
        'service_id', p_service_id,
        'actual_hours', p_actual_hours,
        'completion_status', p_completion_status,
        'labor_cost', p_actual_hours * COALESCE(v_service.hourly_rate, 0),
        'message', 'Servicio completado exitosamente'
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al completar servicio'
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 3. FUNCIONES DE FACTURACIÓN
-- =====================================================

-- Función para generar número de factura (robusta)
CREATE OR REPLACE FUNCTION svc.generate_invoice_number()
RETURNS VARCHAR AS $$
DECLARE
    v_year_month VARCHAR(6);
    v_next_seq INTEGER;
    v_invoice_number VARCHAR(30);
    v_current_year INTEGER;
    v_current_month INTEGER;
BEGIN
    v_current_year := EXTRACT(YEAR FROM CURRENT_DATE);
    v_current_month := EXTRACT(MONTH FROM CURRENT_DATE);
    v_year_month := TO_CHAR(CURRENT_DATE, 'YYYYMM');

    -- Obtener siguiente secuencia para el mes actual
    SELECT COALESCE(MAX(SUBSTRING(invoice_number FROM 9)::INTEGER), 0) + 1
    INTO v_next_seq
    FROM svc.invoices
    WHERE invoice_number LIKE 'INV-' || v_year_month || '-%'
    AND EXTRACT(YEAR FROM created_at) = v_current_year
    AND EXTRACT(MONTH FROM created_at) = v_current_month;

    v_invoice_number := 'INV-' || v_year_month || '-' || LPAD(v_next_seq::TEXT, 4, '0');
    
    RETURN v_invoice_number;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Función para crear factura desde OT
CREATE OR REPLACE FUNCTION svc.create_invoice_from_wo(
    p_wo_id INTEGER,
    p_issue_date DATE DEFAULT CURRENT_DATE,
    p_due_date DATE DEFAULT NULL,
    p_discount_amount DECIMAL DEFAULT 0,
    p_discount_percent DECIMAL DEFAULT 0,
    p_notes TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_wo RECORD;
    v_invoice_number VARCHAR;
    v_invoice_id INTEGER;
    v_total_parts DECIMAL;
    v_total_labor DECIMAL;
    v_subtotal DECIMAL;
    v_result JSONB;
BEGIN
    -- Validar OT
    SELECT wo.*, c.client_id, c.name as client_name
    INTO v_wo
    FROM svc.work_orders wo
    JOIN cat.clients c ON wo.client_id = c.client_id
    WHERE wo.wo_id = p_wo_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Orden de trabajo no encontrada: %', p_wo_id;
    END IF;

    -- Validar que OT esté entregada
    IF v_wo.status != 'ENTREGADO' THEN
        RAISE EXCEPTION 'La OT debe estar en estado ENTREGADO para facturar. Estado actual: %', v_wo.status;
    END IF;

    -- Validar que no exista factura previa
    IF EXISTS (SELECT 1 FROM svc.invoices WHERE wo_id = p_wo_id AND status != 'CANCELLED') THEN
        RAISE EXCEPTION 'Ya existe una factura para esta OT';
    END IF;

    -- Calcular totales
    SELECT COALESCE(SUM(line_total), 0) INTO v_total_parts
    FROM svc.wo_items 
    WHERE wo_id = p_wo_id AND status = 'USED';

    SELECT COALESCE(SUM(labor_cost), 0) INTO v_total_labor
    FROM svc.wo_services 
    WHERE wo_id = p_wo_id AND completion_status IN ('COMPLETED', 'QA_PASSED');

    v_subtotal := v_total_parts + v_total_labor + COALESCE(v_wo.additional_costs, 0);

    -- Aplicar descuentos
    IF p_discount_percent > 0 THEN
        p_discount_amount := v_subtotal * (p_discount_percent / 100);
    END IF;

    -- Generar número de factura
    v_invoice_number := svc.generate_invoice_number();

    -- Crear factura
    INSERT INTO svc.invoices (
        invoice_number,
        wo_id,
        client_id,
        subtotal,
        tax_amount,
        discount_amount,
        total_amount,
        status,
        issue_date,
        due_date,
        notes,
        created_at,
        updated_at
    ) VALUES (
        v_invoice_number,
        p_wo_id,
        v_wo.client_id,
        v_subtotal,
        0, -- tax_amount, se podría calcular si hay impuestos
        p_discount_amount,
        v_subtotal - p_discount_amount,
        'SENT',
        p_issue_date,
        COALESCE(p_due_date, p_issue_date + INTERVAL '30 days'),
        p_notes,
        NOW(),
        NOW()
    ) RETURNING invoice_id INTO v_invoice_id;

    -- Agregar items de partes
    INSERT INTO svc.invoice_items (
        invoice_id,
        internal_sku,
        description,
        qty,
        unit_price,
        tax_percent,
        discount_percent
    )
    SELECT 
        v_invoice_id,
        wi.internal_sku,
        COALESCE(pm.name, 'Parte de repuesto') as description,
        wi.qty_used,
        wi.unit_price,
        0, -- tax_percent
        0  -- discount_percent
    FROM svc.wo_items wi
    LEFT JOIN inv.product_master pm ON wi.internal_sku = pm.internal_sku
    WHERE wi.wo_id = p_wo_id 
    AND wi.status = 'USED'
    AND wi.qty_used > 0;

    -- Agregar items de mano de obra
    INSERT INTO svc.invoice_items (
        invoice_id,
        description,
        qty,
        unit_price,
        tax_percent,
        discount_percent
    )
    SELECT 
        v_invoice_id,
        ws.description,
        ws.actual_hours,
        ws.hourly_rate,
        0, -- tax_percent
        0  -- discount_percent
    FROM svc.wo_services ws
    WHERE ws.wo_id = p_wo_id 
    AND ws.completion_status IN ('COMPLETED', 'QA_PASSED')
    AND ws.actual_hours > 0;

    -- Agregar costos adicionales si existen
    IF v_wo.additional_costs > 0 THEN
        INSERT INTO svc.invoice_items (
            invoice_id,
            description,
            qty,
            unit_price
        ) VALUES (
            v_invoice_id,
            'Costos adicionales',
            1,
            v_wo.additional_costs
        );
    END IF;

    -- Actualizar estado de OT a FACTURACIÓN
    UPDATE svc.work_orders 
    SET status = 'FACTURACIÓN',
        updated_at = NOW()
    WHERE wo_id = p_wo_id;

    v_result := jsonb_build_object(
        'success', true,
        'invoice_id', v_invoice_id,
        'invoice_number', v_invoice_number,
        'subtotal', v_subtotal,
        'discount_amount', p_discount_amount,
        'total_amount', v_subtotal - p_discount_amount,
        'parts_total', v_total_parts,
        'labor_total', v_total_labor,
        'message', 'Factura creada exitosamente'
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al crear factura'
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para registrar pago
CREATE OR REPLACE FUNCTION svc.register_payment(
    p_invoice_id INTEGER,
    p_amount DECIMAL,
    p_payment_method VARCHAR,
    p_payment_date DATE DEFAULT CURRENT_DATE,
    p_reference_number VARCHAR DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    v_invoice RECORD;
    v_total_paid DECIMAL;
    v_payment_id INTEGER;
    v_remaining_amount DECIMAL;
    v_result JSONB;
BEGIN
    -- Validar factura
    SELECT i.*, c.name as client_name
    INTO v_invoice
    FROM svc.invoices i
    JOIN cat.clients c ON i.client_id = c.client_id
    WHERE i.invoice_id = p_invoice_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Factura no encontrada: %', p_invoice_id;
    END IF;

    IF v_invoice.status = 'CANCELLED' THEN
        RAISE EXCEPTION 'No se pueden registrar pagos en facturas canceladas';
    END IF;

    IF v_invoice.status = 'PAID' THEN
        RAISE EXCEPTION 'La factura ya está pagada en su totalidad';
    END IF;

    -- Validar método de pago
    IF p_payment_method NOT IN ('CASH','CARD','TRANSFER','CHECK','OTHER') THEN
        RAISE EXCEPTION 'Método de pago inválido: %', p_payment_method;
    END IF;

    -- Validar monto
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'El monto del pago debe ser mayor a 0: %', p_amount;
    END IF;

    -- Calcular total pagado hasta ahora
    SELECT COALESCE(SUM(amount), 0) INTO v_total_paid
    FROM svc.payments 
    WHERE invoice_id = p_invoice_id;

    v_remaining_amount := v_invoice.total_amount - v_total_paid;

    IF p_amount > v_remaining_amount THEN
        RAISE EXCEPTION 'Monto excede el saldo pendiente. Pendiente: %, Pago: %', 
                       v_remaining_amount, p_amount;
    END IF;

    -- Registrar pago
    INSERT INTO svc.payments (
        invoice_id,
        payment_date,
        amount,
        currency_code,
        payment_method,
        reference_number,
        notes,
        created_at
    ) VALUES (
        p_invoice_id,
        p_payment_date,
        p_amount,
        v_invoice.currency_code,
        p_payment_method,
        p_reference_number,
        p_notes,
        NOW()
    ) RETURNING payment_id INTO v_payment_id;

    -- Verificar si la factura está completamente pagada
    v_total_paid := v_total_paid + p_amount;
    
    IF v_total_paid >= v_invoice.total_amount THEN
        UPDATE svc.invoices 
        SET status = 'PAID',
            paid_date = p_payment_date,
            updated_at = NOW()
        WHERE invoice_id = p_invoice_id;

        -- Actualizar crédito usado del cliente
        UPDATE cat.clients 
        SET credit_used = GREATEST(credit_used - v_invoice.total_amount, 0),
            updated_at = NOW()
        WHERE client_id = v_invoice.client_id;

        -- Marcar OT como CERRADA si corresponde
        UPDATE svc.work_orders 
        SET status = 'CERRADO',
            closed_at = NOW(),
            updated_at = NOW()
        WHERE wo_id = v_invoice.wo_id 
        AND status = 'FACTURACIÓN';
    END IF;

    v_result := jsonb_build_object(
        'success', true,
        'payment_id', v_payment_id,
        'invoice_id', p_invoice_id,
        'amount_paid', p_amount,
        'total_paid', v_total_paid,
        'remaining_amount', v_invoice.total_amount - v_total_paid,
        'invoice_status', CASE 
            WHEN v_total_paid >= v_invoice.total_amount THEN 'PAID'
            ELSE 'PARTIAL'
        END,
        'message', 'Pago registrado exitosamente'
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al registrar pago'
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 4. FUNCIONES DE REPORTES Y ANALÍTICA
-- =====================================================

-- Función para generar reporte de productividad por técnico
CREATE OR REPLACE FUNCTION kpi.generate_technician_productivity_report(
    p_start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_end_date DATE DEFAULT CURRENT_DATE,
    p_technician_id INTEGER DEFAULT NULL
)
RETURNS TABLE (
    technician_id INTEGER,
    technician_name VARCHAR,
    total_orders BIGINT,
    completed_orders BIGINT,
    total_hours DECIMAL,
    efficiency_rate DECIMAL,
    labor_revenue DECIMAL,
    avg_quality_score DECIMAL,
    avg_cycle_time DECIMAL,
    utilization_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH technician_stats AS (
        SELECT 
            t.technician_id,
            t.first_name || ' ' || t.last_name as technician_name,
            COUNT(DISTINCT wo.wo_id) as total_orders,
            COUNT(DISTINCT CASE WHEN wo.status = 'CERRADO' THEN wo.wo_id END) as completed_orders,
            SUM(wo.actual_hours) as total_hours,
            AVG(wo.efficiency_rate) as efficiency_rate,
            SUM(wo.labor_cost) as labor_revenue,
            AVG(km.quality_score) as avg_quality_score,
            AVG(EXTRACT(DAY FROM wo.delivery_date - wo.reception_date)) as avg_cycle_time,
            -- Tasa de utilización (horas trabajadas / horas disponibles)
            CASE 
                WHEN COUNT(DISTINCT DATE(wo.actual_start_date)) > 0 
                THEN ROUND(SUM(wo.actual_hours) / (COUNT(DISTINCT DATE(wo.actual_start_date)) * 8) * 100, 2)
                ELSE 0 
            END as utilization_rate
        FROM cat.technicians t
        LEFT JOIN svc.work_orders wo ON t.technician_id = wo.technician_id
        LEFT JOIN kpi.wo_metrics km ON wo.wo_id = km.wo_id
        WHERE wo.delivery_date BETWEEN p_start_date AND p_end_date
        AND (p_technician_id IS NULL OR t.technician_id = p_technician_id)
        AND t.is_active = TRUE
        GROUP BY t.technician_id, t.first_name, t.last_name
    )
    SELECT * FROM technician_stats
    ORDER BY labor_revenue DESC, efficiency_rate DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para análisis ABC dinámico
CREATE OR REPLACE FUNCTION kpi.analyze_abc_inventory(
    p_category VARCHAR DEFAULT NULL,
    p_min_value DECIMAL DEFAULT 0
)
RETURNS TABLE (
    internal_sku VARCHAR,
    product_name VARCHAR,
    group_name VARCHAR,
    total_value DECIMAL,
    total_quantity BIGINT,
    cumulative_value_pct DECIMAL,
    abc_class VARCHAR,
    recommendation VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH inventory_values AS (
        SELECT 
            pm.internal_sku,
            pm.name as product_name,
            tg.name_es as group_name,
            SUM(s.qty_on_hand * COALESCE(s.unit_cost, pm.standard_cost)) as total_value,
            SUM(s.qty_on_hand) as total_quantity
        FROM inv.product_master pm
        JOIN inv.stock s ON pm.internal_sku = s.internal_sku
        JOIN cat.taxonomy_groups tg ON pm.group_code = tg.group_code
        WHERE pm.is_active = TRUE
        AND (p_category IS NULL OR tg.name_es ILIKE '%' || p_category || '%')
        GROUP BY pm.internal_sku, pm.name, tg.name_es
        HAVING SUM(s.qty_on_hand * COALESCE(s.unit_cost, pm.standard_cost)) >= p_min_value
    ),
    ranked_inventory AS (
        SELECT 
            *,
            SUM(total_value) OVER (ORDER BY total_value DESC) / NULLIF(SUM(total_value) OVER (), 0) as cumulative_pct
        FROM inventory_values
    )
    SELECT 
        internal_sku,
        product_name,
        group_name,
        total_value,
        total_quantity,
        ROUND(cumulative_pct * 100, 2) as cumulative_value_pct,
        CASE 
            WHEN cumulative_pct <= 0.7 THEN 'A'
            WHEN cumulative_pct <= 0.9 THEN 'B'
            ELSE 'C'
        END as abc_class,
        CASE 
            WHEN cumulative_pct <= 0.7 THEN 'Control estricto - Revisión frecuente'
            WHEN cumulative_pct <= 0.9 THEN 'Control normal - Revisión periódica'
            ELSE 'Control mínimo - Revisión ocasional'
        END as recommendation
    FROM ranked_inventory
    ORDER BY total_value DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para pronóstico de demanda
CREATE OR REPLACE FUNCTION kpi.forecast_demand(
    p_sku VARCHAR DEFAULT NULL,
    p_lookback_months INTEGER DEFAULT 12,
    p_forecast_months INTEGER DEFAULT 3
)
RETURNS TABLE (
    internal_sku VARCHAR,
    product_name VARCHAR,
    month DATE,
    historical_avg DECIMAL,
    forecasted_qty DECIMAL,
    confidence_interval_low DECIMAL,
    confidence_interval_high DECIMAL,
    reorder_suggestion VARCHAR
) AS $$
DECLARE
    v_avg_monthly_demand DECIMAL;
    v_std_dev DECIMAL;
    v_lead_time_days INTEGER;
    v_safety_stock DECIMAL;
BEGIN
    RETURN QUERY
    WITH monthly_sales AS (
        SELECT 
            t.internal_sku,
            pm.name as product_name,
            DATE_TRUNC('month', t.txn_date) as month,
            SUM(CASE WHEN t.txn_type = 'OUT' THEN ABS(t.qty) ELSE 0 END) as monthly_qty
        FROM inv.transactions t
        JOIN inv.product_master pm ON t.internal_sku = pm.internal_sku
        WHERE t.txn_date >= CURRENT_DATE - (p_lookback_months || ' months')::INTERVAL
        AND (p_sku IS NULL OR t.internal_sku = p_sku)
        AND t.txn_type = 'OUT'
        GROUP BY t.internal_sku, pm.name, DATE_TRUNC('month', t.txn_date)
    ),
    demand_stats AS (
        SELECT 
            internal_sku,
            product_name,
            AVG(monthly_qty) as avg_monthly_demand,
            STDDEV(monthly_qty) as std_dev_demand
        FROM monthly_sales
        GROUP BY internal_sku, product_name
    ),
    forecast AS (
        SELECT 
            ds.internal_sku,
            ds.product_name,
            GENERATE_SERIES(
                DATE_TRUNC('month', CURRENT_DATE),
                DATE_TRUNC('month', CURRENT_DATE) + (p_forecast_months - 1) * INTERVAL '1 month',
                '1 month'
            ) as month,
            ds.avg_monthly_demand as historical_avg,
            ds.avg_monthly_demand as forecasted_qty,
            GREATEST(ds.avg_monthly_demand - (ds.std_dev_demand * 1.96), 0) as confidence_interval_low,
            ds.avg_monthly_demand + (ds.std_dev_demand * 1.96) as confidence_interval_high
        FROM demand_stats ds
    )
    SELECT 
        f.internal_sku,
        f.product_name,
        f.month::DATE,
        ROUND(f.historical_avg, 2),
        ROUND(f.forecasted_qty, 2),
        ROUND(f.confidence_interval_low, 2),
        ROUND(f.confidence_interval_high, 2),
        CASE 
            WHEN f.forecasted_qty > (SELECT reorder_point FROM inv.product_master WHERE internal_sku = f.internal_sku) 
            THEN 'REORDENAR'
            ELSE 'MANTENER'
        END as reorder_suggestion
    FROM forecast f
    ORDER BY f.internal_sku, f.month;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 5. FUNCIONES DE MANTENIMIENTO Y UTILIDAD
-- =====================================================

-- Función para limpiar datos antiguos (archivado)
CREATE OR REPLACE FUNCTION app.archive_old_data(
    p_table_name VARCHAR,
    p_retention_months INTEGER DEFAULT 24,
    p_dry_run BOOLEAN DEFAULT TRUE
)
RETURNS JSONB AS $$
DECLARE
    v_sql TEXT;
    v_count BIGINT;
    v_result JSONB;
BEGIN
    -- Validar tabla
    IF p_table_name NOT IN ('audit_logs', 'transactions', 'stock') THEN
        RAISE EXCEPTION 'Solo se pueden archivar: audit_logs, transactions, stock';
    END IF;

    -- Construir SQL según tabla
    CASE p_table_name
        WHEN 'audit_logs' THEN
            v_sql := format('
                DELETE FROM app.audit_logs 
                WHERE changed_at < CURRENT_DATE - INTERVAL ''%s months''
                RETURNING audit_id', p_retention_months);
        
        WHEN 'transactions' THEN
            v_sql := format('
                DELETE FROM inv.transactions 
                WHERE txn_date < CURRENT_DATE - INTERVAL ''%s months''
                RETURNING txn_id', p_retention_months);
        
        WHEN 'stock' THEN
            v_sql := format('
                DELETE FROM inv.stock 
                WHERE last_receipt_date < CURRENT_DATE - INTERVAL ''%s months''
                AND qty_on_hand = 0
                RETURNING stock_id', p_retention_months);
    END CASE;

    -- Ejecutar o mostrar
    IF p_dry_run THEN
        EXECUTE 'SELECT COUNT(*) FROM (' || v_sql || ') t' INTO v_count;
        v_result := jsonb_build_object(
            'dry_run', true,
            'table', p_table_name,
            'records_to_delete', v_count,
            'sql', v_sql,
            'message', 'Ejecución en modo prueba'
        );
    ELSE
        EXECUTE v_sql;
        GET DIAGNOSTICS v_count = ROW_COUNT;
        
        v_result := jsonb_build_object(
            'dry_run', false,
            'table', p_table_name,
            'records_deleted', v_count,
            'message', 'Archivado completado exitosamente'
        );
    END IF;

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'sql', v_sql,
            'message', 'Error durante el archivado'
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para sincronizar costos promedio
CREATE OR REPLACE FUNCTION inv.sync_average_costs()
RETURNS JSONB AS $$
DECLARE
    v_updated_count INTEGER;
    v_result JSONB;
BEGIN
    WITH product_costs AS (
        SELECT 
            pm.internal_sku,
            CASE 
                WHEN COUNT(DISTINCT s.unit_cost) > 0 
                THEN ROUND(AVG(s.unit_cost), 2)
                ELSE pm.standard_cost
            END as new_avg_cost,
            CASE 
                WHEN MAX(t.unit_cost) IS NOT NULL 
                THEN MAX(t.unit_cost)
                ELSE pm.last_purchase_cost
            END as new_last_cost
        FROM inv.product_master pm
        LEFT JOIN inv.stock s ON pm.internal_sku = s.internal_sku AND s.qty_on_hand > 0
        LEFT JOIN (
            SELECT internal_sku, unit_cost 
            FROM inv.transactions 
            WHERE txn_type = 'IN' 
            AND txn_date = (SELECT MAX(txn_date) FROM inv.transactions t2 
                           WHERE t2.internal_sku = transactions.internal_sku 
                           AND t2.txn_type = 'IN')
        ) t ON pm.internal_sku = t.internal_sku
        WHERE pm.is_active = TRUE
        GROUP BY pm.internal_sku, pm.standard_cost, pm.last_purchase_cost
    )
    UPDATE inv.product_master pm
    SET avg_cost = pc.new_avg_cost,
        last_purchase_cost = pc.new_last_cost,
        updated_at = NOW()
    FROM product_costs pc
    WHERE pm.internal_sku = pc.internal_sku
    AND (pm.avg_cost != pc.new_avg_cost OR pm.last_purchase_cost != pc.new_last_cost);

    GET DIAGNOSTICS v_updated_count = ROW_COUNT;

    v_result := jsonb_build_object(
        'success', true,
        'products_updated', v_updated_count,
        'timestamp', NOW(),
        'message', 'Costos promedio sincronizados exitosamente'
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al sincronizar costos'
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para verificar integridad de datos
CREATE OR REPLACE FUNCTION app.check_data_integrity()
RETURNS TABLE (
    check_type VARCHAR,
    table_name VARCHAR,
    issue_description TEXT,
    record_count BIGINT,
    severity VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    -- 1. Stock negativo
    SELECT 
        'STOCK_NEGATIVE' as check_type,
        'inv.stock' as table_name,
        'Cantidad en mano negativa' as issue_description,
        COUNT(*) as record_count,
        'CRITICAL' as severity
    FROM inv.stock
    WHERE qty_on_hand < 0
    UNION ALL
    
    -- 2. Reservas mayores que stock disponible
    SELECT 
        'RESERVED_EXCEEDS_STOCK' as check_type,
        'inv.stock' as table_name,
        'Cantidad reservada mayor que stock disponible' as issue_description,
        COUNT(*) as record_count,
        'HIGH' as severity
    FROM inv.stock
    WHERE qty_reserved > qty_on_hand
    UNION ALL
    
    -- 3. OT sin equipo asignado
    SELECT 
        'WO_NO_EQUIPMENT' as check_type,
        'svc.work_orders' as table_name,
        'Orden de trabajo sin equipo asignado' as issue_description,
        COUNT(*) as record_count,
        'HIGH' as severity
    FROM svc.work_orders
    WHERE equipment_id IS NULL
    AND status NOT IN ('CANCELLED')
    UNION ALL
    
    -- 4. Productos sin grupo taxonómico
    SELECT 
        'PRODUCT_NO_GROUP' as check_type,
        'inv.product_master' as table_name,
        'Producto sin grupo taxonómico' as issue_description,
        COUNT(*) as record_count,
        'MEDIUM' as severity
    FROM inv.product_master
    WHERE group_code IS NULL
    AND is_active = TRUE
    UNION ALL
    
    -- 5. Transacciones sin referencia válida
    SELECT 
        'TRANSACTION_NO_REFERENCE' as check_type,
        'inv.transactions' as table_name,
        'Transacción sin referencia válida (WO o PO)' as issue_description,
        COUNT(*) as record_count,
        'MEDIUM' as severity
    FROM inv.transactions
    WHERE reference_number IS NULL
    AND work_order_id IS NULL
    AND purchase_order_id IS NULL
    AND txn_type NOT IN ('ADJUST', 'COUNT')
    UNION ALL
    
    -- 6. Facturas con monto negativo
    SELECT 
        'INVOICE_NEGATIVE_AMOUNT' as check_type,
        'svc.invoices' as table_name,
        'Factura con monto total negativo' as issue_description,
        COUNT(*) as record_count,
        'CRITICAL' as severity
    FROM svc.invoices
    WHERE total_amount < 0
    UNION ALL
    
    -- 7. Pagos mayores que monto de factura
    SELECT 
        'PAYMENT_EXCEEDS_INVOICE' as check_type,
        'svc.payments' as table_name,
        'Pago mayor que monto de factura' as issue_description,
        COUNT(*) as record_count,
        'HIGH' as severity
    FROM svc.payments p
    JOIN svc.invoices i ON p.invoice_id = i.invoice_id
    WHERE p.amount > i.total_amount
    UNION ALL
    
    -- 8. Fechas inconsistentes en OT
    SELECT 
        'WO_DATE_INCONSISTENCY' as check_type,
        'svc.work_orders' as table_name,
        'Fechas inconsistentes (entrega antes de recepción)' as issue_description,
        COUNT(*) as record_count,
        'MEDIUM' as severity
    FROM svc.work_orders
    WHERE delivery_date IS NOT NULL
    AND reception_date IS NOT NULL
    AND delivery_date < reception_date;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 6. STORED PROCEDURES PARA OPERACIONES COMPLEJAS
-- =====================================================

-- Procedimiento para proceso completo de recepción a entrega
CREATE OR REPLACE PROCEDURE svc.complete_work_order_process(
    p_wo_id INTEGER,
    p_technician_id INTEGER,
    p_services JSONB,  -- [{"service_code": "SC001", "actual_hours": 2.5}, ...]
    p_parts_used JSONB, -- [{"sku": "SKU001", "qty": 1}, ...]
    p_final_report TEXT DEFAULT NULL,
    p_qc_notes TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_wo_status VARCHAR;
    v_service_item JSONB;
    v_part_item JSONB;
    v_actual_hours_total DECIMAL := 0;
BEGIN
    -- Validar OT
    SELECT status INTO v_wo_status FROM svc.work_orders WHERE wo_id = p_wo_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Orden de trabajo no encontrada: %', p_wo_id;
    END IF;

    IF v_wo_status NOT IN ('RECEPCIÓN', 'DIAGNÓSTICO') THEN
        RAISE EXCEPTION 'OT debe estar en RECEPCIÓN o DIAGNÓSTICO. Estado actual: %', v_wo_status;
    END IF;

    -- 1. Avanzar a DIAGNÓSTICO si está en RECEPCIÓN
    IF v_wo_status = 'RECEPCIÓN' THEN
        PERFORM svc.advance_work_order_status(p_wo_id, 'DIAGNÓSTICO', p_technician_id);
    END IF;

    -- 2. Avanzar a EN_PROCESO
    PERFORM svc.advance_work_order_status(p_wo_id, 'EN_PROCESO', p_technician_id);

    -- 3. Procesar servicios
    FOR v_service_item IN SELECT * FROM jsonb_array_elements(p_services)
    LOOP
        -- Agregar servicio
        PERFORM svc.add_service_to_wo(
            p_wo_id,
            v_service_item->>'service_code',
            NULL,
            NULL,
            NULL,
            NULL,
            p_technician_id
        );

        -- Completar servicio
        PERFORM svc.complete_service(
            (SELECT service_id FROM svc.wo_services 
             WHERE wo_id = p_wo_id 
             AND service_code = v_service_item->>'service_code'
             ORDER BY created_at DESC LIMIT 1),
            (v_service_item->>'actual_hours')::DECIMAL,
            'COMPLETED',
            'Completado en proceso automático'
        );

        v_actual_hours_total := v_actual_hours_total + (v_service_item->>'actual_hours')::DECIMAL;
    END LOOP;

    -- 4. Procesar partes usadas
    FOR v_part_item IN SELECT * FROM jsonb_array_elements(p_parts_used)
    LOOP
        -- Reservar stock
        PERFORM inv.reserve_stock_for_wo(
            p_wo_id,
            v_part_item->>'sku',
            (v_part_item->>'qty')::DECIMAL
        );

        -- Marcar como usado
        UPDATE svc.wo_items 
        SET qty_used = (v_part_item->>'qty')::DECIMAL,
            status = 'USED',
            used_stock_id = reserved_stock_id,
            updated_at = NOW()
        WHERE wo_id = p_wo_id 
        AND internal_sku = v_part_item->>'sku';
    END LOOP;

    -- 5. Avanzar a QA
    PERFORM svc.advance_work_order_status(p_wo_id, 'QA', p_technician_id, p_qc_notes);

    -- 6. Avanzar a ENTREGADO (asumiendo QA pasa)
    PERFORM svc.advance_work_order_status(p_wo_id, 'ENTREGADO', p_technician_id, p_final_report);

    -- 7. Crear factura automática
    PERFORM svc.create_invoice_from_wo(p_wo_id);

    -- 8. Avanzar a CERRADO (después de facturación)
    PERFORM svc.advance_work_order_status(p_wo_id, 'CERRADO', p_technician_id, 'Proceso completado automáticamente');

    RAISE NOTICE 'Proceso completado para OT %', p_wo_id;
END;
$$;

-- Procedimiento para reabastecimiento automático
CREATE OR REPLACE PROCEDURE inv.auto_replenishment(
    p_supplier_id INTEGER DEFAULT NULL,
    p_min_order_value DECIMAL DEFAULT 100.00,
    p_dry_run BOOLEAN DEFAULT TRUE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_reorder_items RECORD;
    v_po_number VARCHAR;
    v_po_id INTEGER;
    v_total_value DECIMAL := 0;
    v_item_count INTEGER := 0;
BEGIN
    -- Generar número de PO
    v_po_number := 'PO-' || TO_CHAR(NOW(), 'YYYYMM') || '-' || 
                  LPAD((SELECT COUNT(*) + 1 FROM inv.purchase_orders 
                        WHERE EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM NOW())), 4, '0');

    IF p_dry_run THEN
        RAISE NOTICE '=== MODO PRUEBA - No se crearán órdenes de compra ===';
        RAISE NOTICE 'Número de PO que se generaría: %', v_po_number;
    END IF;

    -- Crear PO si no es dry run
    IF NOT p_dry_run THEN
        INSERT INTO inv.purchase_orders (
            po_number,
            supplier_id,
            order_date,
            expected_delivery_date,
            status,
            created_at,
            updated_at
        ) VALUES (
            v_po_number,
            p_supplier_id,
            CURRENT_DATE,
            CURRENT_DATE + INTERVAL '7 days',
            'DRAFT',
            NOW(),
            NOW()
        ) RETURNING po_id INTO v_po_id;
    END IF;

    -- Procesar items que necesitan reorden
    FOR v_reorder_items IN 
        SELECT 
            rn.internal_sku,
            rn.product_name,
            rn.suggested_order_qty,
            rn.primary_supplier,
            pm.last_purchase_cost,
            pm.lead_time_days,
            s.supplier_id
        FROM kpi.reorder_needs rn
        JOIN inv.product_master pm ON rn.internal_sku = pm.internal_sku
        LEFT JOIN cat.suppliers s ON rn.primary_supplier = s.name
        WHERE rn.suggested_order_qty > 0
        AND (p_supplier_id IS NULL OR s.supplier_id = p_supplier_id)
        ORDER BY rn.deficit DESC
    LOOP
        v_total_value := v_total_value + (v_reorder_items.suggested_order_qty * v_reorder_items.last_purchase_cost);
        v_item_count := v_item_count + 1;

        IF p_dry_run THEN
            RAISE NOTICE 'Item: %, Cantidad: %, Costo unitario: %, Subtotal: %, Proveedor: %',
                v_reorder_items.product_name,
                v_reorder_items.suggested_order_qty,
                v_reorder_items.last_purchase_cost,
                v_reorder_items.suggested_order_qty * v_reorder_items.last_purchase_cost,
                v_reorder_items.primary_supplier;
        ELSE
            -- Agregar item al PO
            INSERT INTO inv.po_items (
                po_id,
                internal_sku,
                quantity,
                unit_price,
                notes
            ) VALUES (
                v_po_id,
                v_reorder_items.internal_sku,
                v_reorder_items.suggested_order_qty,
                v_reorder_items.last_purchase_cost,
                'Reorden automática - ' || CURRENT_DATE
            );
        END IF;
    END LOOP;

    -- Validar valor mínimo
    IF v_total_value < p_min_order_value THEN
        IF p_dry_run THEN
            RAISE NOTICE 'Valor total (%%) menor que mínimo requerido (%%) - PO no creada', 
                        v_total_value, p_min_order_value;
        ELSE
            -- Eliminar PO si no alcanza mínimo
            DELETE FROM inv.purchase_orders WHERE po_id = v_po_id;
            RAISE NOTICE 'PO % cancelada - Valor insuficiente', v_po_number;
        END IF;
    ELSE
        IF p_dry_run THEN
            RAISE NOTICE '=== RESUMEN ===';
            RAISE NOTICE 'Items: %, Valor total: %, PO: %', v_item_count, v_total_value, v_po_number;
        ELSE
            -- Actualizar subtotal de PO
            UPDATE inv.purchase_orders 
            SET subtotal = v_total_value,
                updated_at = NOW()
            WHERE po_id = v_po_id;

            RAISE NOTICE 'PO % creada con % items, valor total: %', v_po_number, v_item_count, v_total_value;
        END IF;
    END IF;
END;
$$;

-- =====================================================
-- 7. FUNCIONES DE SEGURIDAD Y ACCESO
-- =====================================================

-- Función para verificar permisos de usuario
CREATE OR REPLACE FUNCTION app.check_user_permission(
    p_user_id INTEGER,
    p_permission VARCHAR,
    p_entity_type VARCHAR DEFAULT NULL,
    p_entity_id INTEGER DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_has_permission BOOLEAN := FALSE;
    v_user_role VARCHAR;
BEGIN
    -- En un sistema real, aquí se consultaría una tabla de roles y permisos
    -- Esta es una implementación simplificada
    SELECT 
        CASE 
            WHEN EXISTS (SELECT 1 FROM cat.technicians WHERE technician_id = p_user_id AND is_active = TRUE) THEN 'TECHNICIAN'
            WHEN p_user_id = 1 THEN 'ADMIN' -- Usuario especial
            ELSE 'GUEST'
        END INTO v_user_role;

    -- Asignar permisos según rol
    CASE v_user_role
        WHEN 'ADMIN' THEN
            v_has_permission := TRUE;
        
        WHEN 'TECHNICIAN' THEN
            v_has_permission := p_permission IN (
                'VIEW_WO', 'UPDATE_WO', 'CREATE_SERVICE', 
                'VIEW_INVENTORY', 'RESERVE_STOCK'
            );
        
        ELSE
            v_has_permission := p_permission IN ('VIEW_OWN_WO', 'VIEW_PROFILE');
    END CASE;

    -- Lógica adicional basada en entidad
    IF p_entity_type = 'WORK_ORDER' AND p_entity_id IS NOT NULL THEN
        -- Verificar si el técnico está asignado a la OT
        IF v_user_role = 'TECHNICIAN' THEN
            SELECT EXISTS (
                SELECT 1 FROM svc.work_orders 
                WHERE wo_id = p_entity_id 
                AND technician_id = p_user_id
            ) INTO v_has_permission;
        END IF;
    END IF;

    RETURN v_has_permission;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para auditar acceso a datos sensibles
CREATE OR REPLACE FUNCTION app.audit_data_access(
    p_user_id INTEGER,
    p_action VARCHAR,
    p_table_name VARCHAR,
    p_record_id BIGINT DEFAULT NULL,
    p_details JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO app.audit_logs (
        table_name,
        record_id,
        action,
        changed_by,
        new_values,
        changed_at
    ) VALUES (
        p_table_name,
        COALESCE(p_record_id, 0),
        p_action,
        p_user_id,
        jsonb_build_object(
            'details', p_details,
            'access_type', p_action,
            'timestamp', NOW()
        ),
        NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- 8. CONFIGURACIÓN FINAL Y ROLES
-- =====================================================

-- Función para inicializar datos del sistema
CREATE OR REPLACE FUNCTION app.initialize_system_data()
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
    v_count INTEGER;
BEGIN
    -- Insertar datos básicos si no existen
    -- Position codes
    INSERT INTO cat.position_codes (position_code, name_es, name_en, category) 
    VALUES 
    ('POS-BOTH', 'Ambos lados', 'Both sides', 'SIDE'),
    ('POS-LH', 'Izquierdo', 'Left-hand', 'SIDE'),
    ('POS-RH', 'Derecho', 'Right-hand', 'SIDE'),
    ('POS-FL', 'Delantero Izquierdo', 'Front Left', 'CORNER'),
    ('POS-FR', 'Delantero Derecho', 'Front Right', 'CORNER'),
    ('POS-RL', 'Trasero Izquierdo', 'Rear Left', 'CORNER'),
    ('POS-RR', 'Trasero Derecho', 'Rear Right', 'CORNER')
    ON CONFLICT (position_code) DO NOTHING;

    -- Source codes
    INSERT INTO cat.source_codes (source_code, name_es, name_en, quality_level) 
    VALUES 
    ('SRC-OEM', 'OEM', 'Original', 'PREMIUM'),
    ('SRC-OES', 'OES', 'OEM Supplier', 'HIGH'),
    ('SRC-AMP', 'Aftermarket Premium', 'Premium Aftermarket', 'HIGH'),
    ('SRC-STD', 'Aftermarket Standard', 'Standard Aftermarket', 'MEDIUM')
    ON CONFLICT (source_code) DO NOTHING;

    -- Condition codes
    INSERT INTO cat.condition_codes (condition_code, name_es, name_en, requires_core) 
    VALUES 
    ('CND-NEW', 'Nuevo', 'New', FALSE),
    ('CND-REMAN', 'Remanufacturado', 'Remanufactured', TRUE),
    ('CND-USED', 'Usado', 'Used', FALSE)
    ON CONFLICT (condition_code) DO NOTHING;

    -- UOM codes
    INSERT INTO cat.uom_codes (uom_code, name_es, name_en, is_fractional, category) 
    VALUES 
    ('EA', 'Pieza', 'Each', FALSE, 'UNIT'),
    ('SET', 'Juego', 'Set', FALSE, 'UNIT'),
    ('L', 'Litro', 'Liter', TRUE, 'VOLUME'),
    ('KG', 'Kilogramo', 'Kilogram', TRUE, 'WEIGHT')
    ON CONFLICT (uom_code) DO NOTHING;

    -- Fuel codes
    INSERT INTO cat.fuel_codes (fuel_code, name_es, name_en, is_alternative) 
    VALUES 
    ('FUEL-GAS', 'Gasolina', 'Gasoline', FALSE),
    ('FUEL-DIE', 'Diésel', 'Diesel', FALSE),
    ('FUEL-HYB', 'Híbrido', 'Hybrid', TRUE)
    ON CONFLICT (fuel_code) DO NOTHING;

    -- Currencies
    INSERT INTO cat.currencies (currency_code, name, symbol, exchange_rate, is_active) 
    VALUES 
    ('USD', 'US Dollar', '$', 1.0, TRUE),
    ('EUR', 'Euro', '€', 1.1, TRUE),
    ('MXN', 'Peso Mexicano', '$', 0.06, TRUE)
    ON CONFLICT (currency_code) DO NOTHING;

    -- Price lists
    INSERT INTO inv.price_lists (price_list_code, name, currency_code, is_active) 
    VALUES 
    ('RETAIL', 'Público General', 'USD', TRUE),
    ('WORKSHOP', 'Talleres Afiliados', 'USD', TRUE),
    ('WHOLESALE', 'Mayoristas', 'USD', TRUE)
    ON CONFLICT (price_list_code) DO NOTHING;

    -- Business rules
    INSERT INTO app.business_rules (rule_code, rule_name, condition_text, action_type, applies_to_table, severity) 
    VALUES 
    ('R01', 'Grupo requerido para producto', 'group_code IS NULL', 'BLOCK', 'product_master', 'HIGH'),
    ('R02', 'Stock mínimo al crear transacción OUT', 
     'NEW.txn_type = ''OUT'' AND EXISTS (SELECT 1 FROM inv.stock s WHERE s.internal_sku = NEW.internal_sku AND s.qty_available < ABS(NEW.qty))', 
     'ALERT', 'transactions', 'HIGH'),
    ('R03', 'WO sin técnico asignado', 
     'NEW.technician_id IS NULL AND NEW.status IN (''EN_PROCESO'', ''QA'')', 
     'ALERT', 'work_orders', 'MEDIUM')
    ON CONFLICT (rule_code) DO NOTHING;

    -- Contar registros insertados
    SELECT COUNT(*) INTO v_count FROM (
        SELECT 1 FROM cat.position_codes
        UNION SELECT 1 FROM cat.source_codes
        UNION SELECT 1 FROM cat.condition_codes
        UNION SELECT 1 FROM cat.uom_codes
        UNION SELECT 1 FROM cat.fuel_codes
        UNION SELECT 1 FROM cat.currencies
        UNION SELECT 1 FROM inv.price_lists
        UNION SELECT 1 FROM app.business_rules
    ) t;

    v_result := jsonb_build_object(
        'success', true,
        'records_initialized', v_count,
        'timestamp', NOW(),
        'message', 'Datos del sistema inicializados exitosamente'
    );

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        v_result := jsonb_build_object(
            'success', false,
            'error', SQLERRM,
            'message', 'Error al inicializar datos del sistema'
        );
        RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Función para obtener estadísticas del sistema
CREATE OR REPLACE FUNCTION app.get_system_stats()
RETURNS JSONB AS $$
DECLARE
    v_stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'clients', (SELECT COUNT(*) FROM cat.clients WHERE status = 'ACTIVE'),
        'technicians', (SELECT COUNT(*) FROM cat.technicians WHERE is_active = TRUE),
        'active_work_orders', (SELECT COUNT(*) FROM svc.work_orders WHERE status NOT IN ('CERRADO', 'CANCELLED')),
        'pending_invoices', (SELECT COUNT(*) FROM svc.invoices WHERE status IN ('SENT', 'OVERDUE')),
        'inventory_items', (SELECT COUNT(*) FROM inv.product_master WHERE is_active = TRUE),
        'total_inventory_value', (SELECT COALESCE(SUM(total_cost), 0) FROM inv.stock),
        'low_stock_items', (SELECT COUNT(*) FROM kpi.critical_stock WHERE critical_level IN ('AGOTADO', 'MÍNIMO')),
        'system_uptime', EXTRACT(EPOCH FROM NOW() - MIN(created_at)) 
                         FROM (SELECT MIN(created_at) FROM svc.work_orders) t
    ) INTO v_stats;

    RETURN v_stats;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;