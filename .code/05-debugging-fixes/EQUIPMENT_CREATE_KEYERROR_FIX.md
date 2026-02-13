# Fix: KeyError 'id' en EquipmentCreateView

**Fecha**: Enero 2026  
**Error**: `KeyError: 'id'` en `EquipmentCreateView.get_context_data` línea 2629

---

## 🔍 **PROBLEMA**

El error ocurría cuando `EquipmentCreateView` intentaba cargar clientes para el dropdown del formulario. El código estaba accediendo directamente a `client['id']`, pero el modelo `Client` usa `client_id` como clave primaria, no `id`.

**Error Original**:
```python
for client in clients_data.get('results', []):
    client_choices.append((client['id'], client['name']))  # KeyError aquí
```

---

## ✅ **SOLUCIÓN**

Se actualizó el código para manejar ambos casos: `client_id` (clave primaria del modelo) e `id` (campo que DRF puede agregar automáticamente).

**Código Corregido**:
```python
for client in clients_data.get('results', []):
    # Handle both 'client_id' (primary key) and 'id' (DRF default)
    client_id = client.get('client_id') or client.get('id')
    client_name = client.get('name', 'Sin nombre')
    if client_id:
        client_choices.append((client_id, client_name))
```

---

## 📝 **ARCHIVOS MODIFICADOS**

### **forge_api/frontend/views.py**

Se corrigieron **7 ubicaciones** donde se accedía a `client['id']`:

1. ✅ **EquipmentCreateView.get_context_data** (línea ~2667)
2. ✅ **EquipmentCreateView.post** (línea ~2686)
3. ✅ **EquipmentUpdateView.get_context_data** (línea ~2779)
4. ✅ **EquipmentUpdateView.post** (línea ~2835)
5. ✅ **WorkOrderListView._get_filter_options** (línea ~925)
6. ✅ **EquipmentListView.get_context_data** (línea ~2412)
7. ✅ **SearchClientsView.get** (línea ~3357)

---

## 🔧 **CAMBIOS APLICADOS**

Todos los accesos a `client['id']` fueron reemplazados por:

```python
client_id = client.get('client_id') or client.get('id')
if client_id:
    # Usar client_id
```

Esto garantiza que:
- ✅ Funciona con `client_id` (campo real del modelo)
- ✅ Funciona con `id` (si DRF lo agrega)
- ✅ Maneja casos donde el campo puede no existir
- ✅ Valida que `client_id` exista antes de usarlo

---

## ✅ **VERIFICACIÓN**

- ✅ Django check: Sin errores
- ✅ Linter: Sin errores
- ✅ Todos los lugares corregidos

---

## 🎯 **RESULTADO**

Ahora `EquipmentCreateView` (y todas las demás vistas que cargan clientes) manejan correctamente ambos formatos de respuesta de la API, evitando el `KeyError: 'id'`.

---

**Estado**: ✅ **CORREGIDO**  
**Fecha**: Enero 2026

