# Plan de Testing - CRUDs de Catalog
**Fecha**: 15 de enero de 2026  
**Tarea**: Testing y validación de Equipment Types, Reference Codes y Currencies

---

## 🎯 Objetivo

Verificar que los 3 CRUDs implementados funcionen correctamente en ambos modos (claro/oscuro), con todas las validaciones y la integración con API.

---

## 📋 Checklist de Testing

### 1. Equipment Types

#### 1.1 Lista
- [ ] URL accesible: `/catalog/equipment-types/`
- [ ] Lista se carga correctamente
- [ ] Búsqueda funciona
- [ ] Filtros funcionan (categoría, estado)
- [ ] Paginación funciona
- [ ] Modo claro: se ve correctamente
- [ ] Modo oscuro: se ve correctamente

#### 1.2 Crear
- [ ] URL accesible: `/catalog/equipment-types/create/`
- [ ] Formulario se carga correctamente
- [ ] Validación de código único funciona
- [ ] Validación de formato de código funciona
- [ ] Validación de JSON schema funciona
- [ ] Creación exitosa redirige a lista
- [ ] Mensaje de éxito se muestra
- [ ] Modo claro: formulario se ve correctamente
- [ ] Modo oscuro: formulario se ve correctamente

#### 1.3 Editar
- [ ] URL accesible: `/catalog/equipment-types/<id>/edit/`
- [ ] Formulario se pre-pobla correctamente
- [ ] Validaciones funcionan
- [ ] Actualización exitosa redirige a lista
- [ ] Mensaje de éxito se muestra
- [ ] Modo claro: formulario se ve correctamente
- [ ] Modo oscuro: formulario se ve correctamente

#### 1.4 Detalle
- [ ] URL accesible: `/catalog/equipment-types/<id>/`
- [ ] Información se muestra correctamente
- [ ] Botones de acción funcionan
- [ ] Modo claro: se ve correctamente
- [ ] Modo oscuro: se ve correctamente

#### 1.5 Eliminar
- [ ] URL accesible: `/catalog/equipment-types/<id>/delete/`
- [ ] Confirmación se muestra correctamente
- [ ] Eliminación exitosa redirige a lista
- [ ] Mensaje de éxito se muestra
- [ ] Modo claro: se ve correctamente
- [ ] Modo oscuro: se ve correctamente

---

### 2. Reference Codes

#### 2.1 Lista
- [ ] URL accesible: `/catalog/reference-codes/`
- [ ] Lista se carga correctamente
- [ ] Sidebar de categorías funciona
- [ ] Búsqueda funciona
- [ ] Filtros funcionan (estado, orden)
- [ ] Navegación entre categorías funciona
- [ ] Modo claro: se ve correctamente
- [ ] Modo oscuro: se ve correctamente

#### 2.2 Crear (por categoría)
- [ ] URL accesible: `/catalog/reference-codes/create/?category=fuel`
- [ ] Formulario se carga con categoría correcta
- [ ] Validación de código único funciona
- [ ] Creación exitosa redirige a lista
- [ ] Mensaje de éxito se muestra
- [ ] Probar en todas las categorías (fuel, transmission, color, etc.)
- [ ] Modo claro: formulario se ve correctamente
- [ ] Modo oscuro: formulario se ve correctamente

#### 2.3 Editar
- [ ] URL accesible: `/catalog/reference-codes/<category>/<id>/edit/`
- [ ] Formulario se pre-pobla correctamente
- [ ] Validaciones funcionan
- [ ] Actualización exitosa redirige a lista
- [ ] Modo claro: formulario se ve correctamente
- [ ] Modo oscuro: formulario se ve correctamente

#### 2.4 Detalle
- [ ] URL accesible: `/catalog/reference-codes/<category>/<id>/`
- [ ] Información se muestra correctamente
- [ ] Verificación de uso funciona
- [ ] Modo claro: se ve correctamente
- [ ] Modo oscuro: se ve correctamente

#### 2.5 Eliminar
- [ ] URL accesible: `/catalog/reference-codes/<category>/<id>/delete/`
- [ ] Confirmación se muestra correctamente
- [ ] Verificación de dependencias funciona
- [ ] Eliminación exitosa redirige a lista
- [ ] Modo claro: se ve correctamente
- [ ] Modo oscuro: se ve correctamente

#### 2.6 Importar/Exportar
- [ ] Importar CSV funciona
- [ ] Exportar CSV funciona
- [ ] Vista previa de importación funciona

---

### 3. Currencies

#### 3.1 Lista
- [ ] URL accesible: `/catalog/currencies/`
- [ ] Lista se carga correctamente
- [ ] Moneda base se identifica correctamente
- [ ] Calculadora de conversión funciona
- [ ] Búsqueda funciona
- [ ] Modo claro: se ve correctamente
- [ ] Modo oscuro: se ve correctamente

#### 3.2 Crear
- [ ] URL accesible: `/catalog/currencies/create/`
- [ ] Formulario se carga correctamente
- [ ] Validación de código ISO 4217 funciona (3 letras)
- [ ] Validación de tipo de cambio > 0 funciona
- [ ] Validación de decimales (0-8) funciona
- [ ] Verificación de código único funciona
- [ ] Creación exitosa redirige a lista
- [ ] Mensaje de éxito se muestra
- [ ] Modo claro: formulario se ve correctamente
- [ ] Modo oscuro: formulario se ve correctamente

#### 3.3 Editar
- [ ] URL accesible: `/catalog/currencies/<code>/edit/`
- [ ] Formulario se pre-pobla correctamente
- [ ] Código no se puede modificar (correcto)
- [ ] Validaciones funcionan
- [ ] Actualización exitosa redirige a lista
- [ ] Mensaje de éxito se muestra
- [ ] Modo claro: formulario se ve correctamente
- [ ] Modo oscuro: formulario se ve correctamente

#### 3.4 Detalle
- [ ] URL accesible: `/catalog/currencies/<code>/`
- [ ] Información se muestra correctamente
- [ ] Tipo de cambio formateado correctamente
- [ ] Moneda base identificada correctamente
- [ ] Botones de acción funcionan
- [ ] Modo claro: se ve correctamente
- [ ] Modo oscuro: se ve correctamente

#### 3.5 Eliminar
- [ ] URL accesible: `/catalog/currencies/<code>/delete/`
- [ ] Confirmación se muestra correctamente
- [ ] Verificación de dependencias funciona
- [ ] Eliminación exitosa redirige a lista
- [ ] Mensaje de éxito se muestra
- [ ] Modo claro: se ve correctamente
- [ ] Modo oscuro: se ve correctamente

---

## 🔍 Validaciones a Probar

### Equipment Types
- [ ] Código único (no duplicados)
- [ ] Formato de código (CATEGORIA-NNN)
- [ ] Categoría válida
- [ ] Nombre requerido
- [ ] JSON schema válido
- [ ] Prefijo de código coincide con categoría

### Reference Codes
- [ ] Código único por categoría
- [ ] Código solo letras, números, guiones
- [ ] Descripción requerida (mínimo 3 caracteres)
- [ ] Código convertido a mayúsculas automáticamente

### Currencies
- [ ] Código ISO 4217 (exactamente 3 letras)
- [ ] Código único
- [ ] Tipo de cambio > 0
- [ ] Decimales entre 0 y 8
- [ ] Nombre requerido

---

## 🌓 Testing de Modos Claro/Oscuro

### Para cada CRUD:
- [ ] Lista se ve correctamente en modo claro
- [ ] Lista se ve correctamente en modo oscuro
- [ ] Formularios se ven correctamente en modo claro
- [ ] Formularios se ven correctamente en modo oscuro
- [ ] Detalles se ven correctamente en modo claro
- [ ] Detalles se ven correctamente en modo oscuro
- [ ] Confirmaciones se ven correctamente en ambos modos
- [ ] No hay gradientes en modo oscuro
- [ ] Contraste adecuado en ambos modos
- [ ] Texto legible en ambos modos

---

## 🔌 Integración con API

### Verificar:
- [ ] Endpoints API responden correctamente
- [ ] Autenticación funciona
- [ ] Manejo de errores de API funciona
- [ ] Mensajes de error son claros
- [ ] Respuestas se procesan correctamente
- [ ] Paginación funciona con API
- [ ] Filtros se envían correctamente a API

---

## 📝 Casos de Prueba Específicos

### Equipment Types
1. **Crear tipo válido**: AUTO-001, Automotriz, "Vehículo Automotriz"
2. **Crear con código duplicado**: Debe mostrar error
3. **Crear con código formato inválido**: Debe mostrar error
4. **Crear con JSON schema inválido**: Debe mostrar error
5. **Editar tipo existente**: Cambiar nombre, descripción
6. **Eliminar tipo sin dependencias**: Debe funcionar
7. **Eliminar tipo con dependencias**: Debe mostrar advertencia

### Reference Codes
1. **Crear código fuel**: DIESEL, "Combustible Diésel"
2. **Crear código duplicado en misma categoría**: Debe mostrar error
3. **Crear código en diferentes categorías**: Debe permitir mismo código
4. **Importar CSV válido**: Debe crear códigos
5. **Importar CSV con duplicados**: Debe manejar correctamente
6. **Exportar CSV**: Debe descargar archivo

### Currencies
1. **Crear moneda base**: USD, exchange_rate = 1.0
2. **Crear moneda adicional**: EUR, exchange_rate = 1.1
3. **Crear con código inválido**: Debe mostrar error (2 letras, 4 letras)
4. **Crear con tipo de cambio <= 0**: Debe mostrar error
5. **Editar tipo de cambio**: Cambiar de 1.1 a 1.2
6. **Eliminar moneda sin dependencias**: Debe funcionar

---

## 🐛 Errores Comunes a Verificar

- [ ] Errores 404 se manejan correctamente
- [ ] Errores 400 (validación) se muestran claramente
- [ ] Errores 500 se manejan gracefully
- [ ] Errores de conexión se muestran claramente
- [ ] Mensajes de error son user-friendly

---

## ✅ Criterios de Éxito

### Funcionalidad
- ✅ Todos los CRUDs funcionan correctamente
- ✅ Todas las validaciones funcionan
- ✅ Integración con API sin errores
- ✅ Manejo de errores adecuado

### Visual
- ✅ Ambos modos (claro/oscuro) funcionan correctamente
- ✅ No hay gradientes en modo oscuro
- ✅ Contraste adecuado en ambos modos
- ✅ UX consistente y profesional

### Performance
- ✅ Carga rápida de páginas
- ✅ Búsqueda y filtros responden rápido
- ✅ Sin errores en consola del navegador

---

## 📊 Resultados del Testing

### Equipment Types
- Estado: ⏳ Pendiente
- Errores encontrados: 
- Notas: 

### Reference Codes
- Estado: ⏳ Pendiente
- Errores encontrados: 
- Notas: 

### Currencies
- Estado: ⏳ Pendiente
- Errores encontrados: 
- Notas: 

---

**Fecha de inicio**: 15 de enero de 2026  
**Estado**: En progreso
