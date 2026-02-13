# Referencia Rápida - Sistema de Reportes

**Última actualización:** 2026-01-15

---

## 🚀 Acceso Rápido (30 segundos)

### Paso 1: Ir a Reportes
```
http://127.0.0.1:8000/catalog/
→ Buscar tarjeta NEGRA (última)
→ Clic en "Ver Reportes"
```

### Paso 2: Abrir Modal de Reportes Programados
```
http://127.0.0.1:8000/catalog/reports/
→ Scroll hasta el FINAL
→ Buscar botón AZUL "Nuevo Reporte Programado"
→ Clic en el botón
→ ✅ Modal se abre
```

---

## 📍 Ubicaciones Clave

| Elemento | URL | Ubicación | Color |
|----------|-----|-----------|-------|
| Tarjeta Reportes | `/catalog/` | Última tarjeta | Negro |
| Botón "Ver Reportes" | `/catalog/` | Dentro de tarjeta negra | Negro |
| Página de Reportes | `/catalog/reports/` | - | - |
| Botón "Nuevo Reporte" | `/catalog/reports/` | Final de página, esquina superior derecha | Azul |
| Modal | `/catalog/reports/` | Se abre al clic | Blanco |

---

## ✅ Estado del Sistema

| Funcionalidad | Estado | Notas |
|---------------|--------|-------|
| Enlace a reportes | ✅ Funciona | Tarjeta negra en `/catalog/` |
| Página de reportes | ✅ Funciona | `/catalog/reports/` |
| Filtros por fecha | ✅ Funciona | Parte superior |
| Gráficos (4) | ✅ Funciona | Chart.js |
| Análisis predictivo | ✅ Funciona | Datos de ejemplo |
| Modal de programación | ✅ Funciona | Frontend completo |
| Exportación PDF | ✅ Funciona | Requiere WeasyPrint |
| Exportación Excel | ✅ Funciona | Requiere openpyxl |
| Guardar reportes | ⚠️ No funciona | Backend pendiente |
| Ejecutar reportes | ⚠️ No funciona | Backend pendiente |
| Enviar por email | ⚠️ No funciona | Backend pendiente |

---

## 🔍 Verificación Rápida

```bash
# 1. Abrir navegador
http://127.0.0.1:8000/catalog/

# 2. ¿Ves tarjeta negra "Estadísticas y Reportes"?
[ ] SÍ → Continuar
[ ] NO → Refresca página (F5)

# 3. Clic en "Ver Reportes"
# 4. ¿Llegaste a /catalog/reports/?
[ ] SÍ → Continuar
[ ] NO → Verificar URL en urls.py

# 5. Scroll hasta el final
# 6. ¿Ves botón azul "Nuevo Reporte Programado"?
[ ] SÍ → Continuar
[ ] NO → Verificar template

# 7. Clic en botón azul
# 8. ¿Se abre el modal?
[ ] SÍ → ✅ TODO FUNCIONA
[ ] NO → Verificar Bootstrap JS (F12)
```

---

## 🚨 Problemas Comunes

| Problema | Solución |
|----------|----------|
| No veo tarjeta negra | Scroll hacia abajo, es la última tarjeta |
| Error 404 en reportes | Verificar `urls.py` tiene ruta `catalog/reports/` |
| No veo botón azul | Scroll hasta el FINAL de `/catalog/reports/` |
| Modal no se abre | Verificar Bootstrap JS en DevTools (F12) |
| Gráficos no aparecen | Verificar Chart.js en DevTools (F12) |

---

## 📚 Documentación Completa

| Documento | Propósito | Tiempo |
|-----------|-----------|--------|
| `INDICE_DOCUMENTACION_REPORTES.md` | Índice maestro | 2 min |
| `RESUMEN_SITUACION_REPORTES.md` | Respuestas a preguntas | 5 min |
| `MAPA_VISUAL_NAVEGACION_REPORTES.md` | Guía visual | 3 min |
| `GUIA_VISUAL_REPORTES_PROGRAMADOS.md` | Guía completa | 10 min |
| `INSTRUCCIONES_VERIFICACION_REPORTES.md` | Checklist | 10 min |
| `RESUMEN_REPORTES_CATALOGO_AVANZADOS.md` | Documentación técnica | 5 min |

---

## 💡 Próximos Pasos

### Opción 1: Verificar Sistema
```
1. Seguir "Verificación Rápida" arriba
2. Reportar resultados
3. Decidir siguiente paso
```

### Opción 2: Implementar Backend
```
1. Crear modelo ScheduledReport
2. Crear API CRUD
3. Configurar Celery
4. Configurar emails
```

### Opción 3: Continuar con Tarea 4
```
1. Leer especificaciones de Tarea 4
2. Implementar gestión de monedas
3. Implementar tasas de cambio
4. Implementar convertidor
```

---

## 📞 Contacto

**Si tienes problemas:**
1. Lee `RESUMEN_SITUACION_REPORTES.md`
2. Sigue `INSTRUCCIONES_VERIFICACION_REPORTES.md`
3. Reporta con captura de pantalla

---

## ✅ Checklist Ultra-Rápido

- [ ] Puedo acceder a `/catalog/`
- [ ] Veo tarjeta negra "Estadísticas y Reportes"
- [ ] Puedo hacer clic en "Ver Reportes"
- [ ] Llego a `/catalog/reports/`
- [ ] Veo filtros, gráficos y estadísticas
- [ ] Veo sección "Reportes Programados" al final
- [ ] Veo botón azul "Nuevo Reporte Programado"
- [ ] El modal se abre al hacer clic
- [ ] Puedo completar el formulario
- [ ] Puedo exportar a PDF/Excel

**Si marcaste todos:** ✅ Sistema funcional  
**Si falta alguno:** ⚠️ Revisar documentación

---

**Estado:** ✅ Referencia Completa  
**Versión:** 1.0
