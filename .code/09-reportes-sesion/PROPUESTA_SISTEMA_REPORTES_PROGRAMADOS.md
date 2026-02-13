# Propuesta - Sistema Completo de Reportes Programados

**Fecha:** 2026-01-13  
**Estado:** 📋 Propuesta  
**Prioridad:** Alta

---

## 🎯 Objetivo

Implementar un sistema completo de reportes programados que permita:
- ✅ Guardar configuraciones en base de datos
- ✅ Ejecutar reportes automáticamente según programación
- ✅ Enviar reportes por email a destinatarios
- ✅ Gestionar historial de ejecuciones
- ✅ Interfaz AJAX moderna sin recargas

---

## 📊 Estado Actual vs Deseado

### Estado Actual (Frontend Only)
- ✅ Modal funcional con formulario completo
- ✅ Validación de campos en cliente
- ✅ Tabla de reportes con ejemplos estáticos
- ❌ No se guardan en base de datos
- ❌ No se ejecutan automáticamente
- ❌ No se envían por email

### Estado Deseado (Sistema Completo)
- ✅ Todo lo anterior +
- ✅ Modelo Django `ScheduledReport`
- ✅ API REST para CRUD de reportes
- ✅ Celery + Celery Beat para ejecución programada
- ✅ Generación de PDF/Excel
- ✅ Envío automático por email
- ✅ Historial de ejecuciones
- ✅ Notificaciones de errores

---

## 🏗️ Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Django Templates)               │
├─────────────────────────────────────────────────────────────┤
│  • Modal de configuración (ya implementado)                 │
│  • Tabla de reportes (actualizar con AJAX)                  │
│  • JavaScript para CRUD sin recargas                        │
└─────────────────────────────────────────────────────────────┘
                              ↓ AJAX
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Django Views/API)                │
├─────────────────────────────────────────────────────────────┤
│  • ScheduledReportCreateView (POST)                         │
│  • ScheduledReportUpdateView (PUT)                          │
│  • ScheduledReportDeleteView (DELETE)                       │
│  • ScheduledReportListView (GET)                            │
│  • ScheduledReportExecuteView (POST - manual)               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    MODELS (Django ORM)                       │
├─────────────────────────────────────────────────────────────┤
│  • ScheduledReport                                          │
│    - name, frequency, time, recipients, format, options     │
│    - user, created_at, active, next_execution               │
│                                                             │
│  • ReportExecution                                          │
│    - scheduled_report, executed_at, status, file_path       │
│    - error_message, execution_time                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    CELERY TASKS                              │
├─────────────────────────────────────────────────────────────┤
│  • execute_scheduled_report(report_id)                      │
│    1. Genera reporte (PDF/Excel)                            │
│    2. Guarda archivo                                        │
│    3. Envía email con adjunto                               │
│    4. Registra ejecución                                    │
│    5. Calcula próxima ejecución                             │
│                                                             │
│  • cleanup_old_reports()                                    │
│    - Elimina archivos antiguos (>90 días)                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    CELERY BEAT (Scheduler)                   │
├─────────────────────────────────────────────────────────────┤
│  • Revisa cada minuto reportes pendientes                   │
│  • Ejecuta reportes según next_execution                    │
│  • Maneja reintentos en caso de fallo                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    EMAIL SERVICE                             │
├─────────────────────────────────────────────────────────────┤
│  • Plantilla HTML profesional                               │
│  • Adjuntos PDF/Excel                                       │
│  • Resumen ejecutivo en cuerpo                              │
│  • Enlace para ver en línea                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Componentes a Implementar

### 1. Modelos Django (2 modelos)

```python
# forge_api/catalog/models.py

class ScheduledReport(models.Model):
    """Configuración de reporte programado"""
    name = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20)  # daily, weekly, monthly, quarterly
    execution_time = models.TimeField()
    recipients = models.TextField()  # emails separados por coma
    format = models.CharField(max_length=10)  # pdf, excel, both
    include_charts = models.BooleanField(default=True)
    include_predictions = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    next_execution = models.DateTimeField()
    
class ReportExecution(models.Model):
    """Historial de ejecuciones"""
    scheduled_report = models.ForeignKey(ScheduledReport, on_delete=models.CASCADE)
    executed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)  # success, failed, running
    file_path = models.CharField(max_length=500, null=True)
    error_message = models.TextField(null=True)
    execution_time = models.FloatField(null=True)  # segundos
```

### 2. Vistas Django (5 vistas)

```python
# forge_api/frontend/views/scheduled_report_views.py

class ScheduledReportCreateView(LoginRequiredMixin, View):
    """Crear nuevo reporte programado (AJAX)"""
    
class ScheduledReportUpdateView(LoginRequiredMixin, View):
    """Actualizar reporte existente (AJAX)"""
    
class ScheduledReportDeleteView(LoginRequiredMixin, View):
    """Eliminar reporte (AJAX)"""
    
class ScheduledReportListView(LoginRequiredMixin, View):
    """Listar reportes del usuario (AJAX)"""
    
class ScheduledReportExecuteView(LoginRequiredMixin, View):
    """Ejecutar reporte manualmente (AJAX)"""
```

### 3. Tareas Celery (3 tareas)

```python
# forge_api/catalog/tasks.py

@shared_task
def execute_scheduled_report(report_id):
    """Ejecuta un reporte programado"""
    # 1. Obtener configuración
    # 2. Generar reporte (PDF/Excel)
    # 3. Guardar archivo
    # 4. Enviar email
    # 5. Registrar ejecución
    # 6. Calcular próxima ejecución
    
@shared_task
def check_pending_reports():
    """Revisa reportes pendientes cada minuto"""
    # Ejecutado por Celery Beat
    
@shared_task
def cleanup_old_reports():
    """Limpia archivos antiguos (diario)"""
    # Ejecutado por Celery Beat
```

### 4. JavaScript AJAX (1 archivo)

```javascript
// forge_api/static/frontend/js/scheduled_reports.js

function saveScheduledReport() {
    // Enviar POST AJAX
    // Actualizar tabla sin recargar
    // Mostrar notificación
}

function editScheduledReport(reportId) {
    // Cargar datos con GET AJAX
    // Llenar formulario
    // Abrir modal
}

function deleteScheduledReport(reportId) {
    // Confirmar
    // Enviar DELETE AJAX
    // Remover fila de tabla
}

function executeScheduledReport(reportId) {
    // Enviar POST AJAX
    // Mostrar progreso
}
```

### 5. Plantillas Email (2 plantillas)

```html
<!-- forge_api/templates/emails/scheduled_report.html -->
Plantilla HTML profesional para emails con reportes
```

---

## 🔧 Dependencias Necesarias

```bash
# Celery para tareas asíncronas
pip install celery redis

# Para generación de reportes (ya instaladas)
pip install weasyprint openpyxl

# Para envío de emails (Django built-in)
# Configurar SMTP en settings.py
```

---

## 📝 Configuración Requerida

### 1. Settings Django

```python
# settings.py

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_BEAT_SCHEDULE = {
    'check-pending-reports': {
        'task': 'catalog.tasks.check_pending_reports',
        'schedule': 60.0,  # cada minuto
    },
    'cleanup-old-reports': {
        'task': 'catalog.tasks.cleanup_old_reports',
        'schedule': crontab(hour=2, minute=0),  # 2 AM diario
    },
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-password'
DEFAULT_FROM_EMAIL = 'ForgeDB <noreply@forgedb.com>'
```

### 2. Celery App

```python
# forge_api/celery.py

from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

app = Celery('forge_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

---

## 🚀 Plan de Implementación

### Fase 1: Modelos y Migraciones (1-2 horas)
- [ ] Crear modelos `ScheduledReport` y `ReportExecution`
- [ ] Crear migraciones
- [ ] Aplicar migraciones
- [ ] Crear admin Django para gestión

### Fase 2: Vistas AJAX (2-3 horas)
- [ ] Implementar `ScheduledReportCreateView`
- [ ] Implementar `ScheduledReportUpdateView`
- [ ] Implementar `ScheduledReportDeleteView`
- [ ] Implementar `ScheduledReportListView`
- [ ] Agregar URLs

### Fase 3: JavaScript Frontend (1-2 horas)
- [ ] Implementar `saveScheduledReport()`
- [ ] Implementar `editScheduledReport()`
- [ ] Implementar `deleteScheduledReport()`
- [ ] Actualizar tabla dinámicamente
- [ ] Agregar notificaciones toast

### Fase 4: Configuración Celery (1 hora)
- [ ] Instalar Redis
- [ ] Configurar Celery
- [ ] Configurar Celery Beat
- [ ] Probar conexión

### Fase 5: Tareas Celery (3-4 horas)
- [ ] Implementar `execute_scheduled_report()`
- [ ] Implementar `check_pending_reports()`
- [ ] Implementar `cleanup_old_reports()`
- [ ] Probar ejecución manual

### Fase 6: Envío de Emails (2 horas)
- [ ] Crear plantilla HTML
- [ ] Configurar SMTP
- [ ] Implementar envío con adjuntos
- [ ] Probar envío

### Fase 7: Testing y Refinamiento (2 horas)
- [ ] Probar flujo completo
- [ ] Manejar errores
- [ ] Agregar logs
- [ ] Documentar

**Tiempo Total Estimado:** 12-16 horas

---

## 💰 Valor de Negocio

### Beneficios:
1. **Automatización:** Elimina trabajo manual de generar reportes
2. **Puntualidad:** Reportes llegan siempre a tiempo
3. **Escalabilidad:** Soporta múltiples reportes y usuarios
4. **Trazabilidad:** Historial completo de ejecuciones
5. **Confiabilidad:** Reintentos automáticos en caso de fallo

### Casos de Uso:
- Reporte diario de inventario a gerencia
- Reporte semanal de proveedores a compras
- Reporte mensual de estadísticas a dirección
- Reporte trimestral de análisis predictivo

---

## ⚠️ Consideraciones

### Requisitos de Infraestructura:
- **Redis:** Necesario para Celery (broker de mensajes)
- **Celery Worker:** Proceso en segundo plano
- **Celery Beat:** Programador de tareas
- **SMTP:** Servidor de correo configurado

### Alternativas Simples (sin Celery):
Si no quieres instalar Celery/Redis, podríamos usar:
- **Django-cron:** Más simple pero menos robusto
- **APScheduler:** Programador en memoria (se pierde al reiniciar)
- **Cron del sistema:** Requiere acceso al servidor

---

## 🎯 Decisión

¿Quieres que implemente el sistema completo con Celery (recomendado) o prefieres una alternativa más simple?

**Opción A: Sistema Completo con Celery** ⭐ Recomendado
- Más robusto y escalable
- Requiere Redis
- Producción-ready

**Opción B: Sistema Simple con Django-cron**
- Más fácil de configurar
- No requiere Redis
- Limitaciones en escalabilidad

**Opción C: Solo Backend sin Ejecución Automática**
- Guardar/editar/eliminar reportes
- Ejecución manual solamente
- Sin emails automáticos

---

**¿Qué opción prefieres?**
