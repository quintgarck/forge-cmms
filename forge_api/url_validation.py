#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validación de URLs CRUD sin conexión a base de datos
Valida que todas las rutas estén correctamente definidas
"""

import os
import django
from django.urls import reverse, NoReverseMatch
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

def validate_urls():
    """Validar que todas las URLs CRUD estén definidas"""
    
    print("=" * 70)
    print("🔍 VALIDACIÓN DE URLs CRUD - SIN CONEXIÓN A BASE DE DATOS")
    print("=" * 70)
    
    # Lista de URLs a validar con sus nombres y descripciones
    url_patterns = [
        # CLIENTES
        ('frontend:client_list', 'Clientes - Lista'),
        ('frontend:client_create', 'Clientes - Crear'),
        ('frontend:client_detail', 'Clientes - Detalle'),
        ('frontend:client_update', 'Clientes - Editar'),
        ('frontend:client_delete', 'Clientes - Eliminar'),
        
        # EQUIPOS
        ('frontend:equipment_list', 'Equipos - Lista'),
        ('frontend:equipment_create', 'Equipos - Crear'),
        ('frontend:equipment_detail', 'Equipos - Detalle'),
        ('frontend:equipment_update', 'Equipos - Editar'),
        ('frontend:equipment_delete', 'Equipos - Eliminar'),
        
        # TIPOS DE EQUIPO (CATÁLOGOS)
        ('frontend:equipment_type_list', 'Tipos Equipo - Lista'),
        ('frontend:equipment_type_create', 'Tipos Equipo - Crear'),
        ('frontend:equipment_type_detail', 'Tipos Equipo - Detalle'),
        ('frontend:equipment_type_edit', 'Tipos Equipo - Editar'),
        ('frontend:equipment_type_delete', 'Tipos Equipo - Eliminar'),
        
        # TAXONOMÍA
        ('frontend:taxonomy_tree', 'Taxonomía - Árbol'),
        ('frontend:taxonomy_system_list', 'Taxonomía - Sistemas Lista'),
        ('frontend:taxonomy_system_create', 'Taxonomía - Sistema Crear'),
        ('frontend:taxonomy_system_detail', 'Taxonomía - Sistema Detalle'),
        ('frontend:taxonomy_system_edit', 'Taxonomía - Sistema Editar'),
        ('frontend:taxonomy_system_delete', 'Taxonomía - Sistema Eliminar'),
        
        # SUBSISTEMAS TAXONOMÍA
        ('frontend:taxonomy_subsystem_list', 'Taxonomía - Subsistemas Lista'),
        ('frontend:taxonomy_subsystem_create', 'Taxonomía - Subsistema Crear'),
        ('frontend:taxonomy_subsystem_detail', 'Taxonomía - Subsistema Detalle'),
        ('frontend:taxonomy_subsystem_edit', 'Taxonomía - Subsistema Editar'),
        ('frontend:taxonomy_subsystem_delete', 'Taxonomía - Subsistema Eliminar'),
        
        # GRUPOS TAXONOMÍA
        ('frontend:taxonomy_group_list', 'Taxonomía - Grupos Lista'),
        ('frontend:taxonomy_group_create', 'Taxonomía - Grupo Crear'),
        ('frontend:taxonomy_group_detail', 'Taxonomía - Grupo Detalle'),
        ('frontend:taxonomy_group_edit', 'Taxonomía - Grupo Editar'),
        ('frontend:taxonomy_group_delete', 'Taxonomía - Grupo Eliminar'),
        
        # CÓDIGOS DE REFERENCIA
        ('frontend:reference_code_list', 'Códigos Ref. - Lista'),
        ('frontend:reference_code_create', 'Códigos Ref. - Crear'),
        ('frontend:reference_code_import', 'Códigos Ref. - Importar'),
        ('frontend:reference_code_export', 'Códigos Ref. - Exportar'),
        ('frontend:reference_code_detail', 'Códigos Ref. - Detalle'),
        ('frontend:reference_code_edit', 'Códigos Ref. - Editar'),
        
        # MONEDAS
        ('frontend:currency_list', 'Monedas - Lista'),
        ('frontend:currency_create', 'Monedas - Crear'),
        ('frontend:currency_detail', 'Monedas - Detalle'),
        ('frontend:currency_edit', 'Monedas - Editar'),
        ('frontend:currency_delete', 'Monedas - Eliminar'),
        
        # GESTIÓN DE TASAS
        ('frontend:currency_rate_management', 'Tasas - Gestión'),
        ('frontend:currency_converter', 'Tasas - Convertidor'),
        ('frontend:currency_history_enhanced', 'Tasas - Histórico'),
        
        # PROVEEDORES
        ('frontend:supplier_list', 'Proveedores - Lista'),
        ('frontend:supplier_create', 'Proveedores - Crear'),
        ('frontend:supplier_detail', 'Proveedores - Detalle'),
        ('frontend:supplier_update', 'Proveedores - Editar'),
        ('frontend:supplier_delete', 'Proveedores - Eliminar'),
        
        # TÉCNICOS
        ('frontend:technician_list', 'Técnicos - Lista'),
        ('frontend:technician_create', 'Técnicos - Crear'),
        ('frontend:technician_detail', 'Técnicos - Detalle'),
        ('frontend:technician_update', 'Técnicos - Editar'),
        ('frontend:technician_delete', 'Técnicos - Eliminar'),
        
        # ÓRDENES DE TRABAJO
        ('frontend:workorder_list', 'Órdenes - Lista'),
        ('frontend:workorder_create', 'Órdenes - Crear'),
        ('frontend:workorder_detail', 'Órdenes - Detalle'),
        ('frontend:workorder_update', 'Órdenes - Editar'),
        ('frontend:workorder_delete', 'Órdenes - Eliminar'),
        
        # FACTURAS
        ('frontend:invoice_list', 'Facturas - Lista'),
        ('frontend:invoice_create', 'Facturas - Crear'),
        ('frontend:invoice_detail', 'Facturas - Detalle'),
        ('frontend:invoice_update', 'Facturas - Editar'),
        ('frontend:invoice_delete', 'Facturas - Eliminar'),
        
        # COTIZACIONES
        ('frontend:quote_list', 'Cotizaciones - Lista'),
        ('frontend:quote_create', 'Cotizaciones - Crear'),
        ('frontend:quote_detail', 'Cotizaciones - Detalle'),
        ('frontend:quote_convert_to_work_order', 'Cotizaciones - Convertir'),
        
        # INVENTARIO - PRODUCTOS
        ('frontend:product_list', 'Productos - Lista'),
        ('frontend:product_create', 'Productos - Crear'),
        ('frontend:product_detail', 'Productos - Detalle'),
        ('frontend:product_update', 'Productos - Editar'),
        
        # ALMACENES
        ('frontend:warehouse_list', 'Almacenes - Lista'),
        ('frontend:warehouse_create', 'Almacenes - Crear'),
        ('frontend:warehouse_detail', 'Almacenes - Detalle'),
        ('frontend:warehouse_update', 'Almacenes - Editar'),
        ('frontend:warehouse_delete', 'Almacenes - Eliminar'),
        
        # STOCK
        ('frontend:stock_list', 'Stock - Lista'),
        ('frontend:stock_dashboard', 'Stock - Dashboard'),
        ('frontend:stock_movements', 'Stock - Movimientos'),
        ('frontend:stock_movement_create', 'Stock - Crear Movimiento'),
        
        # TRANSACCIONES
        ('frontend:transaction_list', 'Transacciones - Lista'),
        
        # REPORTES DE INVENTARIO
        ('frontend:inventory_reports', 'Inventario - Reportes'),
        
        # COMPRAS - ÓRDENES DE COMPRA
        ('frontend:purchase_order_list', 'Órdenes Compra - Lista'),
        ('frontend:purchase_order_create', 'Órdenes Compra - Crear'),
        ('frontend:purchase_order_detail', 'Órdenes Compra - Detalle'),
        ('frontend:purchase_order_update', 'Órdenes Compra - Editar'),
        ('frontend:purchase_order_delete', 'Órdenes Compra - Eliminar'),
        
        # MANTENIMIENTO
        ('frontend:maintenance_list', 'Mantenimiento - Lista'),
        ('frontend:maintenance_calendar', 'Mantenimiento - Calendario'),
        ('frontend:maintenance_create', 'Mantenimiento - Crear'),
        ('frontend:maintenance_detail', 'Mantenimiento - Detalle'),
        ('frontend:maintenance_update', 'Mantenimiento - Editar'),
        ('frontend:maintenance_delete', 'Mantenimiento - Eliminar'),
        ('frontend:maintenance_status_update', 'Mantenimiento - Actualizar Estado'),
        
        # CATÁLOGO GENERAL
        ('frontend:catalog_index', 'Catálogo - Índice'),
        ('frontend:catalog_reports', 'Catálogo - Reportes'),
        
        # SERVICIOS
        ('frontend:service_dashboard', 'Servicios - Dashboard'),
        ('frontend:flat_rate_calculator', 'Servicios - Calculadora'),
        ('frontend:service_alerts_list', 'Servicios - Alertas'),
        ('frontend:service_alert_thresholds', 'Servicios - Umbrales'),
        
        # OEM
        ('frontend:oem_brand_list', 'OEM - Marcas'),
        ('frontend:oem_catalog_list', 'OEM - Catálogo'),
        ('frontend:oem_equivalence_list', 'OEM - Equivalencias'),
        
        # ALERTAS
        ('frontend:alerts_list', 'Alertas - Lista'),
        
        # API ENDPOINTS
        ('frontend:dashboard_data', 'API - Datos Dashboard'),
        ('frontend:kpi_details', 'API - Detalles KPI'),
        ('frontend:search_clients', 'API - Buscar Clientes'),
        ('frontend:search_equipment', 'API - Buscar Equipos'),
        ('frontend:debug_auth', 'API - Debug Auth'),
        
        # DIAGNÓSTICO
        ('frontend:api_diagnostic', 'Diagnóstico - API'),
        ('frontend:client_form_diagnostic', 'Diagnóstico - Form Cliente'),
        ('frontend:client_form_debug', 'Diagnóstico - Debug Form'),
        ('frontend:api_health_check', 'Diagnóstico - Health Check'),
        ('frontend:api_connection_monitor', 'Diagnóstico - Monitor Conexión'),
        ('frontend:api_error_rate_tracking', 'Diagnóstico - Tracking Errores'),
    ]
    
    # Validar cada URL
    total_urls = len(url_patterns)
    valid_urls = 0
    invalid_urls = []
    
    print(f"\n📊 Validando {total_urls} URLs de CRUD...\n")
    
    for url_name, description in url_patterns:
        try:
            url = reverse(url_name)
            print(f"✅ {description:<35} → {url}")
            valid_urls += 1
        except NoReverseMatch as e:
            print(f"❌ {description:<35} → ERROR: {str(e)}")
            invalid_urls.append((url_name, description, str(e)))
        except Exception as e:
            print(f"❌ {description:<35} → EXCEPTION: {str(e)}")
            invalid_urls.append((url_name, description, str(e)))
    
    # Resultado final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 70)
    print(f"✅ URLs válidas:     {valid_urls}")
    print(f"❌ URLs inválidas:   {len(invalid_urls)}")
    print(f"📈 Total evaluadas:  {total_urls}")
    print(f"🎯 Porcentaje éxito: {(valid_urls/total_urls)*100:.1f}%")
    
    if invalid_urls:
        print(f"\n🔧 URLs con problemas ({len(invalid_urls)}):")
        print("-" * 50)
        for url_name, description, error in invalid_urls:
            print(f"• {description}")
            print(f"  URL Name: {url_name}")
            print(f"  Error: {error}\n")
    
    # Conclusión
    if valid_urls == total_urls:
        print("\n🎉 ¡TODAS LAS URLs CRUD VALIDADAS EXITOSAMENTE!")
        print("✅ Sistema de rutas completamente funcional")
        print("🚀 Listo para conectar con frontend")
        return True
    else:
        print(f"\n⚠️  {len(invalid_urls)} URLs necesitan corrección")
        print("🔧 Requiere ajustes en urls.py o nombres de vistas")
        return False

if __name__ == '__main__':
    print("🚀 Iniciando validación de URLs CRUD...")
    
    try:
        success = validate_urls()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error crítico: {str(e)}")
        sys.exit(1)