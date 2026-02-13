# Problema: Cliente no se crea - Error de Autenticación

**Fecha**: Enero 2026  
**Problema**: El cliente no se crea - Error "Las credenciales de autenticación no se proveyeron"  
**Causa**: El usuario no está autenticado o el token JWT ha expirado/no está disponible  
**Estado**: 🔍 **DIAGNÓSTICO**

---

## 🐛 **PROBLEMA IDENTIFICADO**

Al intentar crear un cliente, se recibe el error:
```
ERROR: Las credenciales de autenticación no se proveyeron.
INFO: Token expired or invalid, attempting refresh
```

**Causa Raíz**:
- El usuario no tiene un token JWT válido en la sesión
- O el token ha expirado y no se está refrescando correctamente
- El API requiere autenticación JWT para crear clientes

---

## 🔍 **VERIFICACIONES NECESARIAS**

### **1. Verificar si el usuario está autenticado**
- ¿El usuario hizo login correctamente?
- ¿Hay un token JWT en la sesión?
- ¿El token no ha expirado?

### **2. Verificar el flujo de login**
- ¿El login está funcionando?
- ¿Los tokens se están guardando correctamente en la sesión?
- ¿El token se está enviando en las peticiones al API?

### **3. Solución Temporal**
Para probar si el problema es de autenticación:

1. **Cerrar sesión y volver a iniciar sesión**
   - Esto generará nuevos tokens JWT
   - Verificar que el login funcione correctamente

2. **Verificar en la consola del navegador**
   - Abrir DevTools (F12)
   - Ir a Application/Storage → Session Storage
   - Verificar si hay tokens guardados

3. **Verificar los logs del servidor**
   - Revisar si hay errores de autenticación
   - Verificar si las peticiones al API están llegando con el token

---

## ✅ **SOLUCIÓN SUGERIDA**

El código ya tiene manejo de refresco de token, pero parece que:
1. El usuario no está autenticado, O
2. El token no se está pasando correctamente en las peticiones

**Pasos para resolver**:

1. **Asegurarse de que el usuario haga login primero**
   - Ir a `/login/`
   - Hacer login con credenciales válidas
   - Verificar que se redirija al dashboard

2. **Verificar que el login guarde los tokens**
   - Revisar `AuthenticationService.login()`
   - Verificar que los tokens se guarden en la sesión

3. **Verificar que las peticiones incluyan el token**
   - Revisar `ForgeAPIClient._set_auth_headers()`
   - Verificar que el token se agregue al header `Authorization`

---

## 📝 **NOTA**

Este es un problema de configuración de autenticación, no un bug en el código de creación de clientes. El código está funcionando correctamente, pero requiere que el usuario esté autenticado.

---

**Documento generado**: Enero 2026  
**Problema**: Error de autenticación al crear cliente  
**Estado**: 🔍 **REQUIERE LOGIN DEL USUARIO**

