# Corrección: SerializerMethodField en read_only_fields

**Fecha**: Enero 2026  
**Problema**: `SerializerMethodField` no debe estar en `read_only_fields`

---

## ❌ **ERROR**

Los `SerializerMethodField` estaban incluidos en `read_only_fields`, lo cual es incorrecto:

```python
read_only_fields = [
    'id', 'username', 'date_joined', 'last_login', 'full_name',
    'is_workshop_admin', 'can_manage_inventory', 'can_manage_clients', 'can_view_reports'  # ❌ Error
]
```

## ✅ **SOLUCIÓN**

Los `SerializerMethodField` ya son de solo lectura por defecto y **NO** deben estar en `read_only_fields`. Solo los campos del modelo deben estar ahí:

```python
read_only_fields = [
    'id', 'username', 'date_joined', 'last_login', 'full_name'  # ✅ Solo campos del modelo
]
```

---

## 📝 **NOTA TÉCNICA**

- `SerializerMethodField` ya es de solo lectura por defecto
- `read_only_fields` solo debe contener nombres de campos del modelo
- Los métodos `get_*` para `SerializerMethodField` se definen por separado

---

**Archivo modificado**: `forge_api/core/serializers/auth_serializers.py`

