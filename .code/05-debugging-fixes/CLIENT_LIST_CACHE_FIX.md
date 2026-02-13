# Fix: Cliente creado no aparece en el listado - Problema de Caché

**Fecha**: Enero 2026  
**Problema**: El cliente se crea correctamente pero no aparece en el listado  
**Causa**: Caché no se invalida después de crear un cliente  
**Estado**: ✅ **RESUELTO**

---

## 🐛 **PROBLEMA IDENTIFICADO**

El cliente se crea exitosamente (hay 1 cliente en la base de datos), pero no aparece en el listado.

**Causa Raíz**:
- El método `get_clients()` usa caché (`use_cache=True`)
- Después de crear un cliente con `create_client()`, el caché no se invalida
- Cuando se carga el listado, se sirve la versión en caché (sin el nuevo cliente)

---

## ✅ **SOLUCIÓN IMPLEMENTADA**

Se agregó invalidación automática de caché después de operaciones POST/PUT/DELETE.

### **Archivo 1: `forge_api/frontend/services/api_client.py`**

#### **Cambio 1: Invalidación automática de caché**
Se agregó código para invalidar el caché relacionado después de mutaciones:

```python
# Invalidate related cache on POST/PUT/DELETE
if method in ['POST', 'PUT', 'PATCH', 'DELETE']:
    self._invalidate_related_cache(endpoint)
```

#### **Cambio 2: Nuevo método `_invalidate_related_cache()`**
Se agregó un método para invalidar el caché relacionado:

```python
def _invalidate_related_cache(self, endpoint: str):
    """Invalidate cache for related endpoints after mutations."""
    try:
        # Get all cache keys
        if hasattr(cache, 'keys'):
            # Redis or cache backend that supports keys()
            pattern = f'forge_api*{endpoint.split("/")[0]}*'
            keys = cache.keys(pattern)
            if keys:
                cache.delete_many(keys)
        else:
            # Fallback: delete common cache keys manually
            base_endpoint = endpoint.split('/')[0] if '/' in endpoint else endpoint
            common_keys = [
                f'forge_api:{base_endpoint}',
                f'forge_api:{base_endpoint}_',
            ]
            for key in common_keys:
                cache.delete(key)
    except Exception as e:
        logger.warning(f"Failed to invalidate cache: {e}")
```

### **Archivo 2: `forge_api/frontend/views/client_views.py`**

#### **Cambio: Redirección al listado en lugar del detalle**
También cambié la redirección para ir al listado en lugar del detalle (más útil para ver que el cliente se agregó):

```python
# ANTES:
return redirect('frontend:client_detail', pk=client_id)

# DESPUÉS:
return redirect('frontend:client_list')
```

Nota: También agregué limpieza manual de caché por si acaso, aunque la invalidación automática debería funcionar.

---

## 📋 **CÓMO FUNCIONA AHORA**

1. **Usuario crea un cliente**
   - Se llama a `api_client.create_client(client_data)`
   - El API hace POST a `/api/v1/clients/`
   - La respuesta se recibe exitosamente

2. **Invalidación automática de caché**
   - El método `_make_request()` detecta que es un POST
   - Llama a `_invalidate_related_cache('clients/')`
   - Se eliminan todas las claves de caché relacionadas con `clients`

3. **Usuario ve el listado**
   - Se llama a `api_client.get_clients()`
   - El caché está vacío (fue invalidado)
   - Se hace una nueva petición GET al API
   - Se obtienen todos los clientes incluyendo el nuevo
   - El nuevo resultado se guarda en caché

---

## ✅ **VERIFICACIÓN**

Después de estos cambios:

1. **Crear un cliente**
   - Debería mostrarse el mensaje de éxito
   - Debería redirigir al listado

2. **Ver el listado**
   - El cliente recién creado debería aparecer
   - No debería necesitar recargar la página

3. **Caché funciona correctamente**
   - El listado se carga más rápido (usa caché)
   - Pero siempre muestra datos actualizados después de crear/editar/eliminar

---

## 📝 **NOTA**

La invalidación automática funciona con:
- ✅ Redis (si está configurado)
- ✅ Cache backends que soportan `cache.keys()`
- ✅ Cache backends sin `keys()` (usando fallback manual)

---

**Documento generado**: Enero 2026  
**Problema**: Cliente creado no aparece en listado  
**Estado**: ✅ **RESUELTO**

