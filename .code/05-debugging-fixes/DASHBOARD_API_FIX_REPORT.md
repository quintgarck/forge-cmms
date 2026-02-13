# Fix: Error 404 en Dashboard API - URL Duplicada

**Fecha**: Enero 2026  
**Problema**: Error 404 en `/api/v1//api/dashboard-data/` (URL duplicada)  
**Estado**: ✅ **RESUELTO**

---

## 🐛 **PROBLEMA IDENTIFICADO**

El error mostraba:
```
Failed to load resource: the server responded with a status of 404 (Not Found)
api/v1//api/dashboard-data/
```

**Causa Raíz**:
- El código estaba usando `{% url "frontend:dashboard_data" %}` que genera `/api/dashboard-data/`
- Luego se concatenaba con `ForgeDB.config.apiBaseUrl` que es `/api/v1/`
- Resultado: `/api/v1/` + `/api/dashboard-data/` = `/api/v1//api/dashboard-data/` ❌

---

## ✅ **SOLUCIÓN IMPLEMENTADA**

Se cambió el código para usar directamente el endpoint del API (`dashboard/`) en lugar de la URL completa generada por Django.

### **Archivo**: `forge_api/templates/frontend/dashboard/dashboard.html`

#### **Cambio 1: updateChartPeriod()**
```javascript
// ANTES:
fetch(`{% url "frontend:dashboard_data" %}?${params}`)

// DESPUÉS:
ForgeDB.api.get(`dashboard/?${params}`)
```

#### **Cambio 2: refreshDashboard()**
```javascript
// ANTES:
ForgeDB.api.get('{% url "frontend:dashboard_data" %}')

// DESPUÉS:
ForgeDB.api.get('dashboard/')
```

#### **Cambio 3: showKPIDetails()**
```javascript
// ANTES:
const response = await fetch(`{% url "frontend:kpi_details" kpi_type="PLACEHOLDER" %}`.replace('PLACEHOLDER', kpiType));
const data = await response.json();

// DESPUÉS:
const data = await ForgeDB.api.get(`dashboard/kpi/${kpiType}/`);
```

---

## 📋 **ENDPOINTS CORRECTOS DEL API**

El API backend expone estos endpoints:
- `/api/v1/dashboard/` - Datos del dashboard
- `/api/v1/dashboard/kpi/<kpi_type>/` - Detalles de KPI específico

El código JavaScript ahora usa correctamente:
- `dashboard/` → Se convierte en `/api/v1/dashboard/` (apiBaseUrl + endpoint)
- `dashboard/kpi/${kpiType}/` → Se convierte en `/api/v1/dashboard/kpi/${kpiType}/`

---

## ✅ **VERIFICACIÓN**

Después de estos cambios:

1. **Dashboard debería cargar correctamente**
   - Sin errores 404 en la consola
   - Los datos del dashboard se cargan correctamente

2. **Refresh del dashboard funciona**
   - El botón "Actualizar" funciona sin errores

3. **KPI details funcionan**
   - Los drill-downs de KPIs funcionan correctamente

4. **Chart period update funciona**
   - Cambiar el período de los gráficos funciona sin errores

---

## 📝 **NOTA ADICIONAL**

También hay un error menor con el icono `icon-144x144.png` que no se encuentra, pero esto no afecta la funcionalidad. Si se desea, se puede crear un icono placeholder o removerlo del manifest.

---

**Documento generado**: Enero 2026  
**Problema**: URL duplicada en dashboard API  
**Estado**: ✅ **RESUELTO**

