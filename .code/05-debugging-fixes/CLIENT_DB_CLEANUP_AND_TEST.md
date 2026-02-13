# Limpieza y Diagnóstico: Problema con Clientes

**Fecha**: Enero 2026  
**Problema**: Cliente inválido en BD, listado muestra datos incorrectos, no se pueden crear clientes  
**Estado**: 🔧 **EN DIAGNÓSTICO**

---

## 🐛 **PROBLEMAS IDENTIFICADOS**

### **1. Cliente Inválido en Base de Datos**
- Hay 1 cliente en la BD con `client_code` vacío
- El modelo Client requiere que `client_code` sea único y no vacío
- Este cliente es inválido y puede causar problemas

### **2. El Listado Muestra el Cliente Inválido**
- El API está devolviendo el cliente con código vacío
- El frontend muestra lo que el API devuelve
- Esto es correcto desde el punto de vista del API, pero el dato es inválido

### **3. No Se Pueden Crear Clientes**
- Posibles causas:
  - El formulario no se envía (validación del lado del cliente)
  - Error de autenticación (no hay token JWT válido)
  - Error en el API al crear

---

## ✅ **ACCIONES REALIZADAS**

### **1. Limpieza de Base de Datos**
Se eliminó el cliente inválido (con `client_code` vacío):
```python
Client.objects.filter(client_code='').delete()
```

### **2. Limpieza de Caché**
Se limpió el caché para asegurar que el listado muestre datos actualizados:
```python
cache.clear()
```

---

## 🔍 **PRÓXIMOS PASOS PARA DIAGNÓSTICO**

### **1. Verificar que el Listado Esté Vacío**
1. Recarga la página del listado de clientes
2. Debería estar vacío ahora (0 clientes)
3. Si aún muestra el cliente, hay caché del navegador - presiona Ctrl+F5

### **2. Intentar Crear un Cliente**
1. Ir a `/clients/create/`
2. Llenar todos los campos requeridos:
   - Código de Cliente: TEST001 (o cualquier código único)
   - Tipo: Individual
   - Nombre: Cliente Test
   - Email: test@example.com
   - Teléfono: 1234567890
3. Abrir la consola del navegador (F12 → Console)
4. Intentar crear el cliente
5. Revisar los mensajes en la consola

### **3. Verificar Autenticación**
- **IMPORTANTE**: Debes estar autenticado para crear clientes
- Si no has hecho login, el formulario se enviará pero el API rechazará la petición
- Ve a `/login/` y haz login primero

### **4. Verificar en Network Tab**
1. Abrir DevTools (F12)
2. Ir a la pestaña "Network"
3. Intentar crear un cliente
4. Buscar una petición POST a `/clients/create/` o `/api/v1/clients/`
5. Si no hay petición → El formulario no se está enviando (problema de validación)
6. Si hay petición pero falla → Revisar el error en la petición

---

## 📋 **VERIFICACIONES ADICIONALES**

### **Estado Actual de la BD**
```python
from core.models import Client
print(f'Total clientes: {Client.objects.count()}')  # Debería ser 0
```

### **Verificar API Directamente**
```bash
# Esto requiere un token JWT válido
curl -X GET http://127.0.0.1:8000/api/v1/clients/ \
  -H "Authorization: Bearer <token>"
```

---

## 🎯 **SOLUCIÓN ESPERADA**

Después de la limpieza:
1. ✅ El listado debería estar vacío (0 clientes)
2. ✅ Deberías poder crear nuevos clientes
3. ✅ Los nuevos clientes deberían aparecer en el listado

---

**Documento generado**: Enero 2026  
**Estado**: 🔧 **LIMPIADO - PENDIENTE VERIFICACIÓN**

