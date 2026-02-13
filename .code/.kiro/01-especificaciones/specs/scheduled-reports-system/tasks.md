# Implementation Plan: Sistema de Reportes Programados

## Overview

Plan de implementación para el sistema completo de reportes programados con Celery, Redis, y envío automático de emails. Se implementará en 7 fases incrementales, cada una con validación antes de continuar.

## Tasks

- [ ] 1. Configuración de Infraestructura
- [ ] 1.1 Instalar y configurar Redis
  - Instalar Redis en el sistema
  - Verificar que Redis esté corriendo en puerto 6379
  - Probar conexión con `redis-cli ping`
  - _Requirements: 3.1, 10.7_

- [ ] 1.2 Instalar dependencias Python
  - Instalar celery: `pip install celery[redis]`
  - Instalar redis client: `pip install redis`
  - Verificar instalación con `pip list | grep celery`
  - _Requirements: 3.1_

- [ ] 1.3 Configurar Celery en Django
  - Crear archivo `forge_api/celery.py` con configuración base
  - Agregar configuración CELERY en `settings.py`
  - Configurar CELERY_BROKER_URL y CELERY_RESULT_BACKEND
  - Importar Celery app en `__init__.py`
  - _Requirements: 3.1, 10.1_

- [ ] 1.4 Configurar Celery Beat
  - Agregar CELERY_BEAT_SCHEDULE en `settings.py`
  - Configurar tarea `check_pending_reports` cada 60 segundos
  - Configurar tarea `cleanup_old_reports` diaria a las 2 AM
  - _Requirements: 3.1, 10.3_

- [ ] 1.5 Configurar Email SMTP
  - Agregar configuración EMAIL_* en `settings.py`
  - Configurar EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT
  - Configurar EMAIL_HOST_USER y EMAIL_HOST_PASSWORD
  - Probar envío de email de prueba
  - _Requirements: 5.1, 10.1_

- [ ] 2. Modelos de Base de Datos
- [ ] 2.1 Crear modelo ScheduledReport
  - Crear archivo `forge_api/catalog/models/scheduled_report.py`
  - Definir campos: name, frequency, execution_time, recipients, format, etc.
  - Implementar método `calculate_next_execution()`
  - Implementar método `get_recipients_list()`
  - Agregar Meta class con indexes
  - _Requirements: 2.1, 2.3, 2.4_

- [ ] 2.2 Crear modelo ReportExecution
  - Crear archivo `forge_api/catalog/models/report_execution.py`
  - Definir campos: scheduled_report, started_at, status, file_paths, etc.
  - Agregar relación ForeignKey con ScheduledReport
  - Agregar Meta class con indexes
  - _Requirements: 2.2, 2.5_

- [ ] 2.3 Crear migraciones
  - Ejecutar `python manage.py makemigrations`
  - Revisar archivos de migración generados
  - Ejecutar `python manage.py migrate`
  - Verificar tablas en base de datos
  - _Requirements: 2.1, 2.2_

- [ ] 2.4 Registrar modelos en Django Admin
  - Crear `forge_api/catalog/admin/scheduled_report_admin.py`
  - Registrar ScheduledReport con list_display y filters
  - Registrar ReportExecution con list_display y filters
  - Probar acceso desde /admin/
  - _Requirements: 2.1, 2.2_

- [ ] 3. Servicios de Generación y Email
- [ ] 3.1 Crear ReportGeneratorService
  - Crear archivo `forge_api/catalog/services/report_generator.py`
  - Implementar método `generate_pdf(report_config, execution)`
  - Implementar método `generate_excel(report_config, execution)`
  - Implementar método `_get_catalog_data(report_config)`
  - Reutilizar lógica de CatalogReportExportView
  - _Requirements: 4.1, 4.2, 4.3, 4.6, 4.7_

- [ ] 3.2 Crear EmailService
  - Crear archivo `forge_api/catalog/services/email_service.py`
  - Implementar método `send_report_email(report, execution, files)`
  - Crear plantilla HTML `templates/emails/scheduled_report.html`
  - Implementar adjuntar archivos PDF/Excel
  - Implementar manejo de errores de envío
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [ ] 3.3 Crear plantilla de email HTML
  - Crear `forge_api/templates/emails/scheduled_report.html`
  - Diseño responsive con Bootstrap
  - Incluir resumen ejecutivo del reporte
  - Incluir enlace para ver en línea
  - Incluir información de fecha y hora
  - _Requirements: 5.2, 5.3, 5.4, 5.6, 5.7_

- [ ] 4. Tareas Celery
- [ ] 4.1 Crear tarea execute_scheduled_report
  - Crear archivo `forge_api/catalog/tasks.py`
  - Implementar `@shared_task execute_scheduled_report(report_id)`
  - Implementar flujo: obtener config → generar → enviar → actualizar
  - Implementar manejo de errores con reintentos (máx 3)
  - Implementar logging de cada paso
  - _Requirements: 3.2, 3.3, 3.4, 3.5, 4.1-4.7, 5.1-5.7_

- [ ] 4.2 Crear tarea check_pending_reports
  - Implementar `@shared_task check_pending_reports()`
  - Buscar reportes con next_execution <= now
  - Lanzar execute_scheduled_report para cada uno
  - Implementar logging de reportes encontrados
  - _Requirements: 3.1, 3.2, 3.7_

- [ ] 4.3 Crear tarea cleanup_old_reports
  - Implementar `@shared_task cleanup_old_reports()`
  - Buscar ejecuciones > 90 días
  - Eliminar archivos físicos del disco
  - Limpiar paths en base de datos
  - Implementar logging de archivos eliminados
  - _Requirements: 10.3_

- [ ] 4.4 Probar tareas Celery manualmente
  - Iniciar Celery worker: `celery -A forge_api worker -l info`
  - Iniciar Celery beat: `celery -A forge_api beat -l info`
  - Ejecutar tarea de prueba desde shell Django
  - Verificar logs de ejecución
  - _Requirements: 3.1, 3.5_

- [ ] 5. Vistas Django (API AJAX)
- [ ] 5.1 Crear ScheduledReportCreateView
  - Crear archivo `forge_api/frontend/views/scheduled_report_views.py`
  - Implementar POST handler con validación de datos
  - Validar límite de 10 reportes por usuario
  - Validar formato de emails
  - Calcular next_execution inicial
  - Retornar JSON con report_id y next_execution
  - _Requirements: 1.1, 1.5, 1.6, 1.7, 9.6_

- [ ] 5.2 Crear ScheduledReportUpdateView
  - Implementar PUT handler
  - Verificar permisos (solo creador o admin)
  - Validar datos actualizados
  - Recalcular next_execution
  - Retornar JSON con confirmación
  - _Requirements: 1.2, 9.2, 9.3_

- [ ] 5.3 Crear ScheduledReportDeleteView
  - Implementar DELETE handler
  - Verificar permisos (solo creador o admin)
  - Soft delete (marcar active=False)
  - Cancelar tareas Celery pendientes
  - Retornar JSON con confirmación
  - _Requirements: 1.3, 9.2, 9.3_

- [ ] 5.4 Crear ScheduledReportListView
  - Implementar GET handler
  - Filtrar reportes del usuario actual
  - Incluir estadísticas (total, exitosos, fallidos, tasa de éxito)
  - Serializar a JSON
  - Retornar lista de reportes
  - _Requirements: 1.4_

- [ ] 5.5 Crear ScheduledReportExecuteView
  - Implementar POST handler para ejecución manual
  - Verificar permisos
  - Crear ReportExecution
  - Lanzar tarea Celery inmediatamente
  - Retornar JSON con execution_id y task_id
  - _Requirements: 3.6_

- [ ] 5.6 Crear ScheduledReportDetailView
  - Implementar GET handler para detalle
  - Obtener reporte y últimas 50 ejecuciones
  - Calcular estadísticas agregadas
  - Renderizar template con historial
  - _Requirements: 7.1, 7.2, 7.3, 7.7_

- [ ] 5.7 Agregar URLs para todas las vistas
  - Agregar rutas en `forge_api/frontend/urls.py`
  - POST /catalog/scheduled-reports/create/
  - PUT /catalog/scheduled-reports/<id>/update/
  - DELETE /catalog/scheduled-reports/<id>/delete/
  - GET /catalog/scheduled-reports/list/
  - POST /catalog/scheduled-reports/<id>/execute/
  - GET /catalog/scheduled-reports/<id>/detail/
  - _Requirements: 1.1-1.4, 3.6, 7.1_

- [ ] 6. Frontend JavaScript (AJAX)
- [ ] 6.1 Crear archivo scheduled_reports.js
  - Crear `forge_api/static/frontend/js/scheduled_reports.js`
  - Implementar función `saveScheduledReport()`
  - Implementar función `editScheduledReport(reportId)`
  - Implementar función `deleteScheduledReport(reportId)`
  - Implementar función `executeScheduledReport(reportId)`
  - Implementar función `loadScheduledReports()`
  - _Requirements: 6.1-6.7_

- [ ] 6.2 Implementar saveScheduledReport()
  - Obtener datos del formulario modal
  - Validar campos en cliente
  - Enviar POST AJAX a /create/ o PUT a /update/
  - Mostrar notificación toast de éxito/error
  - Cerrar modal y recargar tabla
  - Deshabilitar botón durante procesamiento
  - _Requirements: 6.1, 6.2, 6.5, 6.6, 6.7_

- [ ] 6.3 Implementar editScheduledReport()
  - Enviar GET AJAX para obtener datos del reporte
  - Llenar formulario del modal con datos
  - Abrir modal en modo edición
  - Cambiar botón "Guardar" por "Actualizar"
  - _Requirements: 6.3_

- [ ] 6.4 Implementar deleteScheduledReport()
  - Mostrar confirmación con SweetAlert o confirm()
  - Enviar DELETE AJAX
  - Remover fila de la tabla sin recargar
  - Mostrar notificación de éxito
  - _Requirements: 6.4, 6.5_

- [ ] 6.5 Implementar loadScheduledReports()
  - Enviar GET AJAX a /list/
  - Limpiar tabla actual
  - Renderizar filas con datos recibidos
  - Agregar event listeners a botones de acción
  - _Requirements: 6.2_

- [ ] 6.6 Actualizar template catalog_reports.html
  - Incluir script scheduled_reports.js
  - Modificar función saveScheduledReport() existente
  - Agregar event listeners para editar/eliminar
  - Agregar notificaciones toast (Bootstrap Toast)
  - _Requirements: 6.1-6.7_

- [ ] 7. Templates y UI
- [ ] 7.1 Crear template scheduled_report_detail.html
  - Crear `forge_api/templates/frontend/catalog/scheduled_report_detail.html`
  - Mostrar información del reporte
  - Mostrar tabla de historial de ejecuciones
  - Mostrar estadísticas agregadas
  - Agregar filtros por estado y fecha
  - Agregar botones para ejecutar manualmente
  - _Requirements: 7.1-7.7_

- [ ] 7.2 Agregar notificaciones toast
  - Agregar HTML para toast container en base.html
  - Crear función JavaScript showToast(message, type)
  - Usar en todas las operaciones AJAX
  - Tipos: success, error, info, warning
  - _Requirements: 6.5_

- [ ] 7.3 Mejorar tabla de reportes programados
  - Actualizar tabla en catalog_reports.html
  - Agregar columna de tasa de éxito
  - Agregar badges de estado (activo/inactivo)
  - Agregar botón "Ver Detalle" por fila
  - Hacer tabla responsive
  - _Requirements: 1.4, 7.1_

- [ ] 8. Testing
- [ ] 8.1 Crear tests unitarios para modelos
  - Crear `forge_api/catalog/tests/test_scheduled_report_model.py`
  - Test calculate_next_execution() para todas las frecuencias
  - Test get_recipients_list() con emails válidos/inválidos
  - Test unique constraint de nombre por usuario
  - _Requirements: 2.1, 2.3, 2.4_

- [ ] 8.2 Crear tests unitarios para vistas
  - Crear `forge_api/frontend/tests/test_scheduled_report_views.py`
  - Test CreateView con datos válidos/inválidos
  - Test UpdateView con permisos correctos/incorrectos
  - Test DeleteView con soft delete
  - Test ListView retorna solo reportes del usuario
  - _Requirements: 1.1-1.4, 9.2, 9.3_

- [ ] 8.3 Crear tests unitarios para servicios
  - Crear `forge_api/catalog/tests/test_report_generator.py`
  - Test generate_pdf() con mock de WeasyPrint
  - Test generate_excel() con mock de openpyxl
  - Test _get_catalog_data() con filtros de fecha
  - _Requirements: 4.1, 4.2, 4.6_

- [ ] 8.4 Crear tests unitarios para email
  - Crear `forge_api/catalog/tests/test_email_service.py`
  - Test send_report_email() con mock de SMTP
  - Test adjuntar archivos PDF/Excel
  - Test manejo de errores de envío
  - _Requirements: 5.1-5.5_

- [ ] 8.5 Crear tests de integración para Celery
  - Crear `forge_api/catalog/tests/test_celery_tasks.py`
  - Test execute_scheduled_report() end-to-end
  - Test check_pending_reports() encuentra reportes
  - Test cleanup_old_reports() elimina archivos
  - Test reintentos en caso de fallo
  - _Requirements: 3.2-3.6, 10.3_

- [ ] 8.6 Crear tests de integración AJAX
  - Crear `forge_api/frontend/tests/test_ajax_workflow.py`
  - Test crear reporte via AJAX
  - Test actualizar reporte via AJAX
  - Test eliminar reporte via AJAX
  - Test cargar lista via AJAX
  - _Requirements: 6.1-6.4_

- [ ] 9. Documentación y Refinamiento
- [ ] 9.1 Crear documentación de usuario
  - Crear `docs/SCHEDULED_REPORTS_USER_GUIDE.md`
  - Explicar cómo crear reportes programados
  - Explicar frecuencias disponibles
  - Explicar formatos de reporte
  - Incluir capturas de pantalla
  - _Requirements: 1.1-1.4_

- [ ] 9.2 Crear documentación técnica
  - Crear `docs/SCHEDULED_REPORTS_TECHNICAL.md`
  - Documentar arquitectura del sistema
  - Documentar modelos y relaciones
  - Documentar tareas Celery
  - Documentar configuración requerida
  - _Requirements: 3.1, 10.1_

- [ ] 9.3 Agregar logging comprehensivo
  - Agregar logs en todas las tareas Celery
  - Agregar logs en servicios de generación
  - Agregar logs en envío de emails
  - Configurar nivel de logs en settings.py
  - _Requirements: 9.4_

- [ ] 9.4 Implementar notificaciones de fallo
  - Crear función notify_report_failure()
  - Enviar email al usuario cuando reporte falla 3 veces
  - Incluir mensaje de error y sugerencias
  - Registrar notificación en logs
  - _Requirements: 8.1, 8.2_

- [ ] 9.5 Crear script de deployment
  - Crear `scripts/deploy_scheduled_reports.sh`
  - Incluir pasos: migraciones, collectstatic, restart services
  - Incluir verificación de Redis
  - Incluir inicio de Celery worker y beat
  - _Requirements: 3.7, 10.7_

- [ ] 10. Checkpoint Final
- Ejecutar todos los tests
- Verificar cobertura de tests (mínimo 85%)
- Probar flujo completo end-to-end
- Verificar que Celery worker y beat estén corriendo
- Verificar que emails se envían correctamente
- Revisar logs por errores
- Documentar cualquier issue pendiente

## Notes

- **Dependencias externas:** Redis debe estar instalado y corriendo antes de iniciar
- **Configuración SMTP:** Requiere credenciales válidas de servidor de correo
- **Archivos generados:** Se guardan en `MEDIA_ROOT/reports/`
- **Retención de archivos:** 90 días por defecto (configurable)
- **Límites:** 10 reportes por usuario, 20 destinatarios por reporte
- **Testing:** Usar pytest con fixtures para Celery y Redis
- **Producción:** Usar supervisor o systemd para mantener Celery worker/beat corriendo

## Estimated Time

- Fase 1 (Infraestructura): 2 horas
- Fase 2 (Modelos): 2 horas
- Fase 3 (Servicios): 3 horas
- Fase 4 (Celery): 3 horas
- Fase 5 (Vistas): 3 horas
- Fase 6 (JavaScript): 2 horas
- Fase 7 (Templates): 1 hora
- Fase 8 (Testing): 3 horas
- Fase 9 (Documentación): 1 hora

**Total: 20 horas**
