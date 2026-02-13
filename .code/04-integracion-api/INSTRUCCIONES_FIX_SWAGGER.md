# Instrucciones: Corregir Error de Swagger

**Fecha**: Enero 2026  
**Problema**: Error 500 al cargar Swagger - "Internal Server Error"

---

## ✅ **CAMBIOS COMPLETADOS**

Se corrigieron dos errores en los serializadores:

1. ✅ `AuditLogSerializer`: `read_only_fields = '__all__'` → Lista explícita
2. ✅ `UserProfileSerializer`: Removido campo `'role'` que no existe en el modelo

---

## 🔄 **PASOS PARA APLICAR LOS CAMBIOS**

### **1. Reiniciar el servidor Django**

Si el servidor está corriendo, **deténlo** (Ctrl+C) y **reinícialo**:

```bash
cd forge_api
python manage.py runserver 8000
```

### **2. Verificar que funciona**

Una vez reiniciado el servidor, visita:
- **Swagger UI**: http://127.0.0.1:8000/swagger/
- **ReDoc**: http://127.0.0.1:8000/redoc/

Deberías ver la documentación completa de la API sin errores.

---

## 📋 **ARCHIVOS MODIFICADOS**

1. **`forge_api/core/serializers/main_serializers.py`**
   - Línea 96: `read_only_fields` de `'__all__'` a lista explícita

2. **`forge_api/core/serializers/auth_serializers.py`**
   - Línea 90: Removido `'role'` de fields
   - Agregados `SerializerMethodField` para propiedades

---

## ✅ **VERIFICACIÓN**

Después de reiniciar el servidor, verifica:

1. ✅ Swagger UI carga sin errores
2. ✅ Los endpoints se muestran correctamente
3. ✅ No hay errores en la consola del servidor
4. ✅ Puedes probar los endpoints desde Swagger

---

**Documento generado**: Enero 2026  
**Estado**: ✅ **Cambios completados - Requiere reinicio del servidor**

