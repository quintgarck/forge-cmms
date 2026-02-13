# Guía de Depuración: Formulario de Cliente No Se Envía

**Fecha**: Enero 2026  
**Problema**: El formulario no se envía - no aparece nada en Network  
**Causa**: Validación del formulario está previniendo el submit

---

## 🔍 **DIAGNÓSTICO**

Si no aparece nada en la pestaña Network cuando intentas crear un cliente, significa que el JavaScript está previniendo el envío del formulario porque la validación está fallando.

### **Pasos para Diagnosticar:**

1. **Abrir la consola del navegador (F12)**
   - Ir a la pestaña "Console"
   - Intentar crear un cliente
   - Deberías ver mensajes como:
     - `Form validation check: false`
     - `Invalid fields: ...`
     - `Invalid field: ...`

2. **Verificar qué campos están inválidos**
   - Los mensajes en la consola te dirán qué campos están fallando
   - Busca mensajes como: `Invalid field: client_code, validity: {...}`

3. **Campos requeridos que deben estar llenos:**
   - **Código de Cliente** (client_code) - Requerido, mínimo 3 caracteres
   - **Tipo de Cliente** (type) - Requerido
   - **Nombre** (name) - Requerido, mínimo 2 caracteres
   - **Email** (email) - Requerido, formato válido
   - **Teléfono** (phone) - Requerido, mínimo 8 dígitos
   - **Límite de Crédito** (credit_limit) - Opcional pero si se llena debe ser un número

---

## ✅ **SOLUCIÓN**

### **Opción 1: Llenar todos los campos requeridos**

Asegúrate de llenar:
- ✅ Código de Cliente (ej: CLI-001, TEST123)
- ✅ Tipo de Cliente (selecciona uno)
- ✅ Nombre completo
- ✅ Email válido (ej: test@example.com)
- ✅ Teléfono (mínimo 8 dígitos, ej: 1234567890)

### **Opción 2: Ver errores de validación en la consola**

He agregado logs de debug. Cuando intentes crear un cliente:
1. Abre la consola (F12 → Console)
2. Intenta crear el cliente
3. Revisa los mensajes en la consola
4. Los mensajes te dirán exactamente qué campos están inválidos y por qué

### **Ejemplo de salida esperada:**

```
Form validation check: false
Invalid fields: NodeList(2) [input#id_client_code.form-control, input#id_email.form-control]
Invalid field: client_code, validity: ValidityState {...}
Invalid field: email, validity: ValidityState {...}
Focusing on first invalid field: client_code
```

---

## 🔧 **VALIDACIONES QUE SE APLICAN**

### **Código de Cliente (client_code):**
- ✅ Requerido
- ✅ Mínimo 3 caracteres
- ✅ Solo letras mayúsculas, números, guiones y guiones bajos
- ✅ Se convierte automáticamente a mayúsculas

### **Nombre (name):**
- ✅ Requerido
- ✅ Mínimo 2 caracteres
- ✅ Solo letras, espacios, guiones y apostrofes

### **Email (email):**
- ✅ Requerido
- ✅ Formato de email válido (ejemplo@dominio.com)
- ✅ Debe contener exactamente un símbolo @

### **Teléfono (phone):**
- ✅ Requerido
- ✅ Mínimo 8 dígitos (después de remover caracteres especiales)

### **Dirección (address):**
- ⚠️ Opcional
- ✅ Si se llena, mínimo 10 caracteres

### **Límite de Crédito (credit_limit):**
- ⚠️ Opcional
- ✅ Si se llena, debe ser un número positivo
- ✅ Máximo $999,999.99

---

## 📝 **NOTA IMPORTANTE**

El formulario usa validación HTML5 del lado del cliente. Si algún campo no pasa la validación, el formulario NO se enviará y NO verás nada en Network.

**Esto es comportamiento normal y esperado** - es una validación preventiva para evitar enviar datos inválidos al servidor.

---

**Documento generado**: Enero 2026  
**Problema**: Formulario no se envía  
**Solución**: Llenar todos los campos requeridos correctamente

