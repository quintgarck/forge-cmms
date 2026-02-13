# Flujo de Cotizaciones, Órdenes de Trabajo y Facturas

## 📊 Flujo del Sistema MovIAx

### Flujo Principal

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│   COTIZACIÓN    │ ──────▶ │ ORDEN DE TRABAJO │ ──────▶ │  FACTURA    │
│   (Presupuesto) │         │   (Trabajo)      │         │  (Cobro)    │
└─────────────────┘         └──────────────────┘         └─────────────┘
     OPCIONAL                      OBLIGATORIA               OBLIGATORIA
```

## 🔄 Detalles del Flujo

### 1️⃣ COTIZACIÓN (Quote) - Opcional

**Propósito**: Estimación/Presupuesto para el cliente

**Estados posibles**:
- `DRAFT` - Borrador
- `SENT` - Enviada al cliente
- `APPROVED` - Aprobada por el cliente
- `REJECTED` - Rechazada
- `EXPIRED` - Expirada
- `CONVERTED` - Convertida a Orden de Trabajo ✅ (Cerrada)

**Características**:
- No genera factura directamente
- Es una **estimación** de costos
- Puede ser convertida a Orden de Trabajo
- Una vez convertida, se marca como `CONVERTED`

### 2️⃣ ORDEN DE TRABAJO (Work Order) - Obligatoria

**Propósito**: Ejecución real del trabajo

**Puede originarse de dos formas**:

#### A) Desde una Cotización (Flujo con Cotización)
```
Cotización (APPROVED) 
    ↓ [Convertir]
Orden de Trabajo
```

#### B) Directamente (Flujo sin Cotización)
```
Cliente solicita trabajo
    ↓ [Crear directamente]
Orden de Trabajo
```

**Estados posibles**:
- `DRAFT` - Borrador
- `SCHEDULED` - Programada
- `IN_PROGRESS` - En progreso
- `COMPLETED` - Completada
- `ENTREGADO` - Entregada al cliente ✅ (Lista para facturar)

**Características**:
- Es la ejecución real del trabajo
- Registra partes usadas, horas trabajadas, servicios completados
- Solo cuando está en estado `ENTREGADO` se puede facturar

### 3️⃣ FACTURA (Invoice) - Obligatoria para cobro

**Propósito**: Documento de cobro al cliente

**Siempre proviene de**:
```
Orden de Trabajo (ESTADO: ENTREGADO)
    ↓ [Generar Factura]
Factura
```

**NUNCA proviene directamente de**:
- ❌ Cotización (no puede facturarse sin ejecutar el trabajo)
- ❌ Creación manual sin WO (el sistema requiere WO)

**Características**:
- Se calcula desde la WO completada:
  - Partes usadas (`wo_items` con status `USED`)
  - Servicios completados (`wo_services` con status `COMPLETED` o `QA_PASSED`)
  - Costos adicionales
- Estado `ENTREGADO` es obligatorio para generar factura
- Una WO solo puede generar una factura (validación en el sistema)

## 📋 Flujos Completos

### Flujo 1: Con Cotización (Flujo Completo)
```
1. Crear Cotización (DRAFT)
   └─> Enviar al cliente (SENT)
       └─> Cliente aprueba (APPROVED)
           └─> [Convertir a WO]
2. Orden de Trabajo creada (DRAFT)
   └─> Programar trabajo (SCHEDULED)
       └─> Ejecutar trabajo (IN_PROGRESS)
           └─> Completar trabajo (COMPLETED)
               └─> Entregar al cliente (ENTREGADO)
                   └─> [Generar Factura]
3. Factura creada (DRAFT)
   └─> Enviar factura (SENT)
       └─> Cliente paga (PAID) ✅
```

### Flujo 2: Sin Cotización (Flujo Directo)
```
1. Cliente solicita trabajo
   └─> [Crear Orden de Trabajo directamente] (DRAFT)
2. Orden de Trabajo (DRAFT)
   └─> Programar trabajo (SCHEDULED)
       └─> Ejecutar trabajo (IN_PROGRESS)
           └─> Completar trabajo (COMPLETED)
               └─> Entregar al cliente (ENTREGADO)
                   └─> [Generar Factura]
3. Factura creada (DRAFT)
   └─> Enviar factura (SENT)
       └─> Cliente paga (PAID) ✅
```

## 🔗 Relaciones en Base de Datos

### Estructura de Referencias

```sql
-- Cotización puede referenciar a una WO (cuando se convierte)
svc.quotes.converted_to_wo_id → svc.work_orders.wo_id

-- Factura siempre referencia a una WO
svc.invoices.wo_id → svc.work_orders.wo_id

-- Factura NO referencia directamente a Cotización
-- (La relación es indirecta: Quote → WO → Invoice)
```

### Diagrama de Relaciones

```
┌─────────────┐
│   Quote     │
│  (cot_id)   │
└──────┬──────┘
       │ converted_to_wo_id (OPCIONAL)
       │
       ▼
┌──────────────────┐
│  Work Order      │ ◄───┐
│  (wo_id)         │     │
└──────┬───────────┘     │
       │ wo_id           │ wo_id
       │                 │
       ▼                 │
┌─────────────┐          │
│  Invoice    │          │
│ (invoice_id)│          │
└─────────────┘          │
                         │
                    ┌────┴─────┐
                    │  Invoice │
                    │ (puede   │
                    │  tener   │
                    │  wo_id)  │
                    └──────────┘
```

## ✅ Resumen de Preguntas

### ¿Las órdenes de trabajo provienen de una factura o una cotización?

**Respuesta**: Las órdenes de trabajo pueden provenir de:
1. **Cotización** (convertir cotización aprobada a WO) ✅
2. **Creación directa** (sin cotización previa) ✅
3. **NO provienen de facturas** ❌ (las facturas vienen DESPUÉS)

### ¿Luego de la orden de trabajo se genera la factura?

**Respuesta**: ✅ **SÍ, correcto**

El flujo es:
```
Orden de Trabajo (estado: ENTREGADO) → Factura
```

**Condiciones para generar factura desde WO**:
- ✅ WO debe estar en estado `ENTREGADO`
- ✅ No debe existir factura previa para esa WO
- ✅ La factura se calcula desde:
  - Partes usadas en la WO
  - Servicios completados
  - Horas trabajadas
  - Costos adicionales

## 🎯 Puntos Clave

1. **Cotización**: Es opcional, es una estimación
2. **Orden de Trabajo**: Es obligatoria, es la ejecución real
3. **Factura**: Se genera DESPUÉS de completar y entregar el trabajo
4. **Flujo**: `Cotización (opcional) → Orden de Trabajo → Factura`
5. **Relación**: Las facturas siempre tienen un `wo_id`, pueden o no tener una cotización previa
