# Requirements Document - Sistema de Reportes Programados

## Introduction

Sistema completo de reportes programados para ForgeDB que permite a los usuarios configurar, gestionar y recibir reportes automáticos del sistema de catálogos por correo electrónico. El sistema incluye persistencia en base de datos, ejecución programada mediante tareas asíncronas, y envío automático de reportes en múltiples formatos.

## Glossary

- **Scheduled_Report**: Configuración de un reporte que se ejecuta automáticamente según una frecuencia definida
- **Report_Execution**: Registro de una ejecución individual de un reporte programado
- **Celery**: Sistema de tareas asíncronas distribuidas para Python/Django
- **Celery_Beat**: Programador de tareas periódicas para Celery
- **Email_Service**: Servicio de envío de correos electrónicos con reportes adjuntos
- **Report_Generator**: Componente que genera reportes en formato PDF o Excel
- **Frequency**: Periodicidad de ejecución (diario, semanal, mensual, trimestral)
- **Recipient**: Destinatario de correo electrónico que recibirá el reporte
- **Report_Format**: Formato del reporte (PDF, Excel, o ambos)

## Requirements

### Requirement 1: Gestión de Reportes Programados

**User Story:** Como usuario del sistema, quiero crear, editar y eliminar reportes programados, para que pueda automatizar la generación y envío de reportes sin intervención manual.

#### Acceptance Criteria

1. WHEN un usuario crea un reporte programado con datos válidos, THE System SHALL guardar la configuración en la base de datos y retornar confirmación
2. WHEN un usuario edita un reporte programado existente, THE System SHALL actualizar la configuración y reprogramar la siguiente ejecución
3. WHEN un usuario elimina un reporte programado, THE System SHALL cancelar todas las ejecuciones futuras y marcar el reporte como inactivo
4. WHEN un usuario lista los reportes programados, THE System SHALL mostrar todos los reportes con su estado, próxima ejecución y destinatarios
5. THE System SHALL validar que el nombre del reporte sea único por usuario
6. THE System SHALL validar que los emails de destinatarios tengan formato válido
7. THE System SHALL validar que la hora de ejecución esté en formato HH:MM válido

### Requirement 2: Modelo de Datos

**User Story:** Como desarrollador, quiero un modelo de datos robusto para reportes programados, para que el sistema pueda almacenar y gestionar configuraciones de manera eficiente.

#### Acceptance Criteria

1. THE Scheduled_Report_Model SHALL incluir campos: nombre, frecuencia, hora_ejecucion, destinatarios, formato, opciones, usuario_creador, fecha_creacion, activo, proxima_ejecucion
2. THE Report_Execution_Model SHALL incluir campos: reporte_programado, fecha_ejecucion, estado, archivo_generado, error_mensaje, tiempo_ejecucion
3. WHEN se crea un reporte programado, THE System SHALL calcular automáticamente la próxima fecha de ejecución
4. WHEN se actualiza la frecuencia de un reporte, THE System SHALL recalcular la próxima fecha de ejecución
5. THE System SHALL mantener un historial de todas las ejecuciones de cada reporte
6. THE System SHALL permitir múltiples destinatarios separados por comas

### Requirement 3: Ejecución Programada con Celery

**User Story:** Como administrador del sistema, quiero que los reportes se ejecuten automáticamente según su programación, para que los usuarios reciban reportes sin intervención manual.

#### Acceptance Criteria

1. THE System SHALL utilizar Celery Beat para programar la ejecución de reportes
2. WHEN llega la hora programada de un reporte, THE System SHALL ejecutar una tarea Celery para generar el reporte
3. WHEN un reporte se ejecuta exitosamente, THE System SHALL actualizar la próxima fecha de ejecución
4. IF un reporte falla durante la ejecución, THE System SHALL registrar el error y reintentar hasta 3 veces
5. THE System SHALL ejecutar reportes en segundo plano sin bloquear otras operaciones
6. THE System SHALL permitir ejecución manual inmediata de cualquier reporte programado
7. WHEN se reinicia el servidor, THE System SHALL reprogramar todos los reportes activos automáticamente

### Requirement 4: Generación de Reportes

**User Story:** Como usuario, quiero que los reportes se generen en el formato que especifiqué, para que pueda usar los datos según mis necesidades.

#### Acceptance Criteria

1. WHEN un reporte se ejecuta con formato PDF, THE System SHALL generar un archivo PDF con todas las estadísticas y gráficos
2. WHEN un reporte se ejecuta con formato Excel, THE System SHALL generar un archivo XLSX con múltiples hojas de datos
3. WHEN un reporte se ejecuta con formato "ambos", THE System SHALL generar tanto PDF como Excel
4. IF la opción "incluir gráficos" está activa, THE System SHALL incluir visualizaciones en el reporte
5. IF la opción "incluir análisis predictivo" está activa, THE System SHALL incluir insights y predicciones
6. THE System SHALL aplicar los filtros de fecha configurados al generar el reporte
7. THE System SHALL nombrar los archivos con formato: `reporte_{nombre}_{fecha}_{hora}.{extension}`

### Requirement 5: Envío de Reportes por Email

**User Story:** Como usuario, quiero recibir los reportes por correo electrónico, para que pueda acceder a ellos sin necesidad de entrar al sistema.

#### Acceptance Criteria

1. WHEN un reporte se genera exitosamente, THE System SHALL enviar un email a todos los destinatarios configurados
2. THE Email SHALL incluir el reporte como archivo adjunto
3. THE Email SHALL incluir un resumen ejecutivo en el cuerpo del mensaje
4. THE Email SHALL incluir la fecha y hora de generación del reporte
5. IF el envío de email falla, THE System SHALL registrar el error y reintentar hasta 3 veces
6. THE System SHALL usar plantillas HTML profesionales para los emails
7. THE System SHALL incluir un enlace para ver el reporte en línea en el sistema

### Requirement 6: Interfaz de Usuario AJAX

**User Story:** Como usuario, quiero gestionar reportes programados sin recargar la página, para que la experiencia sea fluida y moderna.

#### Acceptance Criteria

1. WHEN un usuario guarda un nuevo reporte desde el modal, THE System SHALL enviar una petición AJAX al backend
2. WHEN la petición es exitosa, THE System SHALL cerrar el modal y actualizar la tabla sin recargar la página
3. WHEN un usuario edita un reporte, THE System SHALL cargar los datos en el modal mediante AJAX
4. WHEN un usuario elimina un reporte, THE System SHALL mostrar confirmación y eliminar la fila de la tabla sin recargar
5. THE System SHALL mostrar mensajes de éxito/error usando notificaciones toast
6. THE System SHALL validar el formulario en el cliente antes de enviar al servidor
7. THE System SHALL deshabilitar el botón de guardar mientras se procesa la petición

### Requirement 7: Historial de Ejecuciones

**User Story:** Como usuario, quiero ver el historial de ejecuciones de mis reportes, para que pueda verificar que se están generando correctamente.

#### Acceptance Criteria

1. WHEN un usuario accede al detalle de un reporte programado, THE System SHALL mostrar las últimas 50 ejecuciones
2. THE System SHALL mostrar para cada ejecución: fecha, estado, tiempo de ejecución, y enlace de descarga
3. WHEN una ejecución fue exitosa, THE System SHALL permitir descargar el archivo generado
4. WHEN una ejecución falló, THE System SHALL mostrar el mensaje de error
5. THE System SHALL permitir filtrar ejecuciones por estado (exitoso, fallido, en proceso)
6. THE System SHALL permitir filtrar ejecuciones por rango de fechas
7. THE System SHALL mostrar estadísticas: total de ejecuciones, tasa de éxito, tiempo promedio

### Requirement 8: Notificaciones y Alertas

**User Story:** Como usuario, quiero recibir notificaciones cuando un reporte falla, para que pueda tomar acción correctiva.

#### Acceptance Criteria

1. WHEN un reporte falla después de 3 reintentos, THE System SHALL enviar un email de notificación al usuario creador
2. THE Notification_Email SHALL incluir el mensaje de error y sugerencias de solución
3. WHEN un reporte está inactivo por más de 30 días, THE System SHALL enviar un recordatorio al usuario
4. THE System SHALL permitir al usuario configurar preferencias de notificaciones
5. THE System SHALL mostrar alertas en el dashboard cuando hay reportes fallidos
6. THE System SHALL permitir al usuario desactivar notificaciones para reportes específicos

### Requirement 9: Seguridad y Permisos

**User Story:** Como administrador, quiero controlar quién puede crear y gestionar reportes programados, para que solo usuarios autorizados tengan acceso.

#### Acceptance Criteria

1. THE System SHALL requerir autenticación para acceder a la funcionalidad de reportes programados
2. THE System SHALL permitir solo al creador del reporte editarlo o eliminarlo
3. WHERE el usuario tiene rol de administrador, THE System SHALL permitir gestionar todos los reportes
4. THE System SHALL registrar en logs todas las operaciones de creación, edición y eliminación de reportes
5. THE System SHALL validar que el usuario tenga permisos para acceder a los datos del reporte
6. THE System SHALL limitar el número de reportes programados por usuario (máximo 10)
7. THE System SHALL limitar el número de destinatarios por reporte (máximo 20)

### Requirement 10: Configuración del Sistema

**User Story:** Como administrador del sistema, quiero configurar parámetros globales de reportes programados, para que el sistema funcione según las políticas de la organización.

#### Acceptance Criteria

1. THE System SHALL permitir configurar el servidor SMTP para envío de emails
2. THE System SHALL permitir configurar el número máximo de reintentos para reportes fallidos
3. THE System SHALL permitir configurar el tiempo de retención de archivos generados (por defecto 90 días)
4. THE System SHALL permitir configurar el tamaño máximo de archivos adjuntos en emails
5. THE System SHALL permitir configurar horarios de mantenimiento donde no se ejecutan reportes
6. THE System SHALL permitir configurar plantillas de email personalizadas
7. THE System SHALL validar la configuración de Celery al iniciar el sistema
