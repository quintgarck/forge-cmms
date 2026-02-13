# Corrección Masiva de Templates - MovIAx

**Fecha:** 15 de enero de 2026

## 🔍 Archivos Detectados con Template Antiguo

### Módulo Services (4 archivos activos)
- workorder_timeline.html
- service_dashboard.html
- service_checklist_interactive.html
- flat_rate_calculator.html

### Módulo Catalog (20+ archivos)
- equipment_type_*.html
- taxonomy_*.html
- reference_code_*.html
- currency_list.html
- supplier_advanced_list.html

### Módulo Inventory (13 archivos)
- product_*.html
- stock_*.html
- warehouse_*.html
- transaction_list.html
- dashboard.html

### Módulo Maintenance (4 archivos)
- maintenance_*.html

## ✅ Corrección Necesaria

Todos estos archivos necesitan:
1. Cambiar: `{% extends 'frontend/base.html' %}` → `{% extends 'frontend/base/base.html' %}`
2. Agregar: `{% block body_class %}[module]-page{% endblock %}`

Donde `[module]` es:
- services → `service-page`
- catalog → `catalog-page`
- inventory → `inventory-page`
- maintenance → `maintenance-page`
