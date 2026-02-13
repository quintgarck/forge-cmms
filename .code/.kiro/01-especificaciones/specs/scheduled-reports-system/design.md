# Design Document - Sistema de Reportes Programados

## Overview

Sistema completo de reportes programados que permite a los usuarios configurar, gestionar y recibir reportes automáticos del sistema de catálogos por correo electrónico. Utiliza Celery + Redis para ejecución asíncrona, Django ORM para persistencia, y SMTP para envío de emails.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  • Django Templates (Modal + Tabla)                         │
│  • JavaScript AJAX (CRUD sin recargas)                      │
│  • Bootstrap 5 (UI Components)                              │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP/AJAX
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  • ScheduledReportViews (CRUD API)                          │
│  • ReportGeneratorService                                   │
│  • EmailService                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                              │
│  • ScheduledReport (Model)                                  │
│  • ReportExecution (Model)                                  │
│  • Business Logic                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                      │
│  • Celery Tasks (Async Execution)                           │
│  • Celery Beat (Scheduler)                                  │
│  • Redis (Message Broker)                                   │
│  • Django ORM (Database)                                    │
│  • SMTP (Email Delivery)                                    │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Action → AJAX Request → Django View → Database
                                    ↓
                            Celery Task (async)
                                    ↓
                    Generate Report → Save File → Send Email
                                    ↓
                            Update Database → Log Execution
```

## Components and Interfaces

### 1. Models (Django ORM)

#### ScheduledReport Model

```python
class ScheduledReport(models.Model):
    """
    Configuración de un reporte programado.
    Almacena toda la información necesaria para generar y enviar reportes automáticamente.
    """
    # Identificación
    name = models.CharField(
        max_length=200,
        help_text="Nombre descriptivo del reporte"
    )
    
    # Programación
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Diario'),
            ('weekly', 'Semanal'),
            ('monthly', 'Mensual'),
            ('quarterly', 'Trimestral'),
        ]
    )
    execution_time = models.TimeField(
        help_text="Hora del día para ejecutar (HH:MM)"
    )
    next_execution = models.DateTimeField(
        help_text="Próxima fecha/hora de ejecución calculada"
    )
    
    # Destinatarios
    recipients = models.TextField(
        help_text="Emails separados por coma"
    )
    
    # Formato y Opciones
    format = models.CharField(
        max_length=10,
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('both', 'Ambos'),
        ],
        default='pdf'
    )
    include_charts = models.BooleanField(default=True)
    include_predictions = models.BooleanField(default=False)
    
    # Filtros de Fecha (opcional)
    date_filter_type = models.CharField(
        max_length=20,
        choices=[
            ('last_7_days', 'Últimos 7 días'),
            ('last_30_days', 'Últimos 30 días'),
            ('last_90_days', 'Últimos 90 días'),
            ('current_month', 'Mes actual'),
            ('last_month', 'Mes anterior'),
        ],
        null=True,
        blank=True
    )
    
    # Auditoría
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='scheduled_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    # Estadísticas
    total_executions = models.IntegerField(default=0)
    successful_executions = models.IntegerField(default=0)
    failed_executions = models.IntegerField(default=0)
    last_execution_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'scheduled_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['active', 'next_execution']),
            models.Index(fields=['user', 'active']),
        ]
    
    def calculate_next_execution(self):
        """Calcula la próxima fecha de ejecución basada en frecuencia"""
        pass
    
    def get_recipients_list(self):
        """Retorna lista de emails validados"""
        pass
```

#### ReportExecution Model

```python
class ReportExecution(models.Model):
    """
    Registro de una ejecución individual de un reporte programado.
    Mantiene historial completo para auditoría y debugging.
    """
    scheduled_report = models.ForeignKey(
        ScheduledReport,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_time = models.FloatField(
        null=True,
        help_text="Tiempo de ejecución en segundos"
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=[
            ('running', 'En Ejecución'),
            ('success', 'Exitoso'),
            ('failed', 'Fallido'),
            ('cancelled', 'Cancelado'),
        ],
        default='running'
    )
    
    # Archivos Generados
    pdf_file_path = models.CharField(max_length=500, null=True, blank=True)
    excel_file_path = models.CharField(max_length=500, null=True, blank=True)
    file_size = models.IntegerField(
        null=True,
        help_text="Tamaño total en bytes"
    )
    
    # Email
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_error = models.TextField(null=True, blank=True)
    
    # Errores
    error_message = models.TextField(null=True, blank=True)
    error_traceback = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Celery
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'report_executions'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['scheduled_report', '-started_at']),
            models.Index(fields=['status']),
        ]
```

### 2. Views (Django Class-Based Views)

#### ScheduledReportCreateView

```python
class ScheduledReportCreateView(LoginRequiredMixin, View):
    """
    Crea un nuevo reporte programado.
    Endpoint: POST /catalog/scheduled-reports/create/
    """
    
    def post(self, request):
        """
        Request Body (JSON):
        {
            "name": "Reporte Diario",
            "frequency": "daily",
            "execution_time": "08:00",
            "recipients": "admin@example.com, user@example.com",
            "format": "pdf",
            "include_charts": true,
            "include_predictions": false,
            "date_filter_type": "last_30_days"
        }
        
        Response (JSON):
        {
            "success": true,
            "report_id": 123,
            "message": "Reporte programado creado exitosamente",
            "next_execution": "2026-01-14T08:00:00Z"
        }
        """
        # 1. Validar datos
        # 2. Validar límite de reportes por usuario (máx 10)
        # 3. Validar emails
        # 4. Crear ScheduledReport
        # 5. Calcular next_execution
        # 6. Retornar JSON
        pass
```

#### ScheduledReportUpdateView

```python
class ScheduledReportUpdateView(LoginRequiredMixin, View):
    """
    Actualiza un reporte programado existente.
    Endpoint: PUT /catalog/scheduled-reports/<id>/update/
    """
    
    def put(self, request, report_id):
        """
        Request Body (JSON): Mismo que Create
        
        Response (JSON):
        {
            "success": true,
            "message": "Reporte actualizado exitosamente",
            "next_execution": "2026-01-14T08:00:00Z"
        }
        """
        # 1. Verificar permisos (solo creador o admin)
        # 2. Validar datos
        # 3. Actualizar ScheduledReport
        # 4. Recalcular next_execution
        # 5. Retornar JSON
        pass
```

#### ScheduledReportDeleteView

```python
class ScheduledReportDeleteView(LoginRequiredMixin, View):
    """
    Elimina (desactiva) un reporte programado.
    Endpoint: DELETE /catalog/scheduled-reports/<id>/delete/
    """
    
    def delete(self, request, report_id):
        """
        Response (JSON):
        {
            "success": true,
            "message": "Reporte eliminado exitosamente"
        }
        """
        # 1. Verificar permisos
        # 2. Marcar como inactivo (soft delete)
        # 3. Cancelar tareas Celery pendientes
        # 4. Retornar JSON
        pass
```

#### ScheduledReportListView

```python
class ScheduledReportListView(LoginRequiredMixin, View):
    """
    Lista todos los reportes programados del usuario.
    Endpoint: GET /catalog/scheduled-reports/list/
    """
    
    def get(self, request):
        """
        Response (JSON):
        {
            "success": true,
            "reports": [
                {
                    "id": 1,
                    "name": "Reporte Diario",
                    "frequency": "daily",
                    "frequency_display": "Diario",
                    "execution_time": "08:00",
                    "next_execution": "2026-01-14T08:00:00Z",
                    "recipients": "admin@example.com",
                    "format": "pdf",
                    "active": true,
                    "total_executions": 45,
                    "successful_executions": 43,
                    "failed_executions": 2,
                    "success_rate": 95.6
                }
            ]
        }
        """
        # 1. Obtener reportes del usuario
        # 2. Serializar datos
        # 3. Retornar JSON
        pass
```

#### ScheduledReportExecuteView

```python
class ScheduledReportExecuteView(LoginRequiredMixin, View):
    """
    Ejecuta un reporte manualmente (inmediato).
    Endpoint: POST /catalog/scheduled-reports/<id>/execute/
    """
    
    def post(self, request, report_id):
        """
        Response (JSON):
        {
            "success": true,
            "message": "Reporte en ejecución",
            "execution_id": 456,
            "task_id": "celery-task-uuid"
        }
        """
        # 1. Verificar permisos
        # 2. Crear ReportExecution
        # 3. Lanzar tarea Celery
        # 4. Retornar JSON
        pass
```

#### ScheduledReportDetailView

```python
class ScheduledReportDetailView(LoginRequiredMixin, TemplateView):
    """
    Muestra detalle de un reporte con historial de ejecuciones.
    Endpoint: GET /catalog/scheduled-reports/<id>/detail/
    """
    template_name = 'frontend/catalog/scheduled_report_detail.html'
    
    def get_context_data(self, **kwargs):
        """
        Context:
        - report: ScheduledReport instance
        - executions: últimas 50 ejecuciones
        - statistics: estadísticas agregadas
        """
        pass
```

### 3. Celery Tasks

#### execute_scheduled_report

```python
@shared_task(bind=True, max_retries=3)
def execute_scheduled_report(self, report_id):
    """
    Tarea principal que ejecuta un reporte programado.
    
    Flujo:
    1. Obtener configuración del reporte
    2. Crear registro de ejecución
    3. Generar reporte (PDF/Excel)
    4. Guardar archivos
    5. Enviar email con adjuntos
    6. Actualizar estadísticas
    7. Calcular próxima ejecución
    
    Manejo de Errores:
    - Reintentos automáticos (máx 3)
    - Registro de errores en ReportExecution
    - Notificación al usuario en caso de fallo final
    """
    execution = None
    try:
        # 1. Obtener reporte
        report = ScheduledReport.objects.get(id=report_id, active=True)
        
        # 2. Crear ejecución
        execution = ReportExecution.objects.create(
            scheduled_report=report,
            celery_task_id=self.request.id,
            status='running'
        )
        
        # 3. Generar reporte
        files = generate_report(report, execution)
        
        # 4. Enviar email
        send_report_email(report, execution, files)
        
        # 5. Marcar como exitoso
        execution.status = 'success'
        execution.completed_at = timezone.now()
        execution.save()
        
        # 6. Actualizar estadísticas
        report.total_executions += 1
        report.successful_executions += 1
        report.last_execution_at = timezone.now()
        report.next_execution = report.calculate_next_execution()
        report.save()
        
    except Exception as exc:
        # Registrar error
        if execution:
            execution.status = 'failed'
            execution.error_message = str(exc)
            execution.error_traceback = traceback.format_exc()
            execution.retry_count = self.request.retries
            execution.save()
        
        # Reintentar
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        else:
            # Notificar fallo final
            notify_report_failure(report, execution, exc)
```

#### check_pending_reports

```python
@shared_task
def check_pending_reports():
    """
    Tarea ejecutada cada minuto por Celery Beat.
    Busca reportes cuya next_execution haya llegado y los ejecuta.
    """
    now = timezone.now()
    pending_reports = ScheduledReport.objects.filter(
        active=True,
        next_execution__lte=now
    )
    
    for report in pending_reports:
        # Lanzar tarea de ejecución
        execute_scheduled_report.delay(report.id)
```

#### cleanup_old_reports

```python
@shared_task
def cleanup_old_reports():
    """
    Tarea ejecutada diariamente a las 2 AM.
    Elimina archivos de reportes antiguos (>90 días).
    """
    cutoff_date = timezone.now() - timedelta(days=90)
    old_executions = ReportExecution.objects.filter(
        started_at__lt=cutoff_date,
        status='success'
    )
    
    for execution in old_executions:
        # Eliminar archivos físicos
        if execution.pdf_file_path:
            os.remove(execution.pdf_file_path)
        if execution.excel_file_path:
            os.remove(execution.excel_file_path)
        
        # Limpiar paths en BD
        execution.pdf_file_path = None
        execution.excel_file_path = None
        execution.save()
```

### 4. Services

#### ReportGeneratorService

```python
class ReportGeneratorService:
    """
    Servicio para generar reportes en diferentes formatos.
    Reutiliza la lógica existente de CatalogReportExportView.
    """
    
    def generate_pdf(self, report_config, execution):
        """
        Genera reporte en formato PDF.
        
        Returns:
            str: Path del archivo generado
        """
        # 1. Obtener datos del catálogo
        data = self._get_catalog_data(report_config)
        
        # 2. Renderizar template HTML
        html = render_to_string('reports/catalog_report_pdf.html', data)
        
        # 3. Convertir a PDF con WeasyPrint
        pdf_file = HTML(string=html).write_pdf()
        
        # 4. Guardar archivo
        filename = f"reporte_{report_config.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, 'reports', filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_file)
        
        return filepath
    
    def generate_excel(self, report_config, execution):
        """
        Genera reporte en formato Excel.
        
        Returns:
            str: Path del archivo generado
        """
        # Similar a generate_pdf pero usando openpyxl
        pass
    
    def _get_catalog_data(self, report_config):
        """
        Obtiene datos del catálogo aplicando filtros de fecha.
        """
        # Reutilizar lógica de CatalogReportsView
        pass
```

#### EmailService

```python
class EmailService:
    """
    Servicio para envío de emails con reportes adjuntos.
    """
    
    def send_report_email(self, report, execution, files):
        """
        Envía email con reporte adjunto.
        
        Args:
            report: ScheduledReport instance
            execution: ReportExecution instance
            files: dict con paths de archivos {'pdf': path, 'excel': path}
        """
        # 1. Preparar contexto
        context = {
            'report_name': report.name,
            'execution_date': execution.started_at,
            'user_name': report.user.get_full_name(),
        }
        
        # 2. Renderizar template HTML
        html_content = render_to_string('emails/scheduled_report.html', context)
        
        # 3. Crear email
        email = EmailMultiAlternatives(
            subject=f'Reporte Programado: {report.name}',
            body=strip_tags(html_content),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=report.get_recipients_list()
        )
        email.attach_alternative(html_content, "text/html")
        
        # 4. Adjuntar archivos
        if files.get('pdf'):
            email.attach_file(files['pdf'])
        if files.get('excel'):
            email.attach_file(files['excel'])
        
        # 5. Enviar
        email.send()
        
        # 6. Registrar envío
        execution.email_sent = True
        execution.email_sent_at = timezone.now()
        execution.save()
```

## Data Models

### Database Schema

```sql
-- Tabla: scheduled_reports
CREATE TABLE scheduled_reports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    execution_time TIME NOT NULL,
    next_execution TIMESTAMP NOT NULL,
    recipients TEXT NOT NULL,
    format VARCHAR(10) NOT NULL DEFAULT 'pdf',
    include_charts BOOLEAN DEFAULT TRUE,
    include_predictions BOOLEAN DEFAULT FALSE,
    date_filter_type VARCHAR(20),
    user_id INTEGER NOT NULL REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    last_execution_at TIMESTAMP,
    
    CONSTRAINT unique_report_name_per_user UNIQUE(user_id, name)
);

CREATE INDEX idx_active_next_execution ON scheduled_reports(active, next_execution);
CREATE INDEX idx_user_active ON scheduled_reports(user_id, active);

-- Tabla: report_executions
CREATE TABLE report_executions (
    id SERIAL PRIMARY KEY,
    scheduled_report_id INTEGER NOT NULL REFERENCES scheduled_reports(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time FLOAT,
    status VARCHAR(20) DEFAULT 'running',
    pdf_file_path VARCHAR(500),
    excel_file_path VARCHAR(500),
    file_size INTEGER,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    email_error TEXT,
    error_message TEXT,
    error_traceback TEXT,
    retry_count INTEGER DEFAULT 0,
    celery_task_id VARCHAR(255)
);

CREATE INDEX idx_report_started ON report_executions(scheduled_report_id, started_at DESC);
CREATE INDEX idx_status ON report_executions(status);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Unique Report Names Per User
*For any* user, all active scheduled reports must have unique names within that user's scope.
**Validates: Requirements 1.5**

### Property 2: Valid Email Format
*For any* scheduled report, all recipient emails must conform to valid email format (RFC 5322).
**Validates: Requirements 1.6**

### Property 3: Next Execution Calculation
*For any* scheduled report with frequency F and time T, the next_execution must be correctly calculated as the next occurrence of T according to F from the current time.
**Validates: Requirements 2.3, 2.4**

### Property 4: Execution Retry Limit
*For any* failed report execution, the system must retry at most 3 times before marking as permanently failed.
**Validates: Requirements 3.4**

### Property 5: File Generation Consistency
*For any* report execution with format "both", both PDF and Excel files must be generated or both must fail (atomic operation).
**Validates: Requirements 4.3**

### Property 6: Email Delivery Guarantee
*For any* successful report generation, an email must be sent to all configured recipients or the execution must be marked as failed.
**Validates: Requirements 5.1, 5.5**

### Property 7: Execution History Integrity
*For any* scheduled report, the sum of successful_executions and failed_executions must equal total_executions.
**Validates: Requirements 2.5**

### Property 8: Permission Enforcement
*For any* update or delete operation on a scheduled report, only the creator or an admin user can perform the operation.
**Validates: Requirements 9.2, 9.3**

### Property 9: Report Limit Per User
*For any* user, the total number of active scheduled reports must not exceed 10.
**Validates: Requirements 9.6**

### Property 10: File Cleanup Consistency
*For any* report execution older than 90 days, the associated files must be deleted from disk and the file paths must be cleared from the database.
**Validates: Requirements 10.3**

## Error Handling

### Error Categories

1. **Validation Errors** (HTTP 400)
   - Invalid email format
   - Invalid time format
   - Missing required fields
   - Duplicate report name
   - User report limit exceeded

2. **Permission Errors** (HTTP 403)
   - User not authenticated
   - User not owner of report
   - User not admin

3. **Not Found Errors** (HTTP 404)
   - Report ID doesn't exist
   - Execution ID doesn't exist

4. **Generation Errors** (Celery Task)
   - PDF generation failed
   - Excel generation failed
   - Data query timeout
   - Insufficient disk space

5. **Email Errors** (Celery Task)
   - SMTP connection failed
   - Invalid recipient
   - Attachment too large
   - Email quota exceeded

### Error Handling Strategy

```python
# Vista: Retornar JSON con error
{
    "success": false,
    "error": "Validation error",
    "details": {
        "recipients": ["Invalid email format: invalid@"]
    }
}

# Celery Task: Reintentar con backoff exponencial
try:
    execute_report()
except TemporaryError as e:
    # Reintentar en 1min, 2min, 4min
    self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
except PermanentError as e:
    # No reintentar, notificar usuario
    notify_user(report, error=e)
    raise
```

## Testing Strategy

### Unit Tests

Test specific components in isolation:

1. **Model Tests**
   - Test `calculate_next_execution()` for all frequencies
   - Test `get_recipients_list()` validation
   - Test unique constraint enforcement

2. **View Tests**
   - Test CRUD operations with valid data
   - Test validation errors
   - Test permission checks
   - Test JSON response format

3. **Service Tests**
   - Test PDF generation with mock data
   - Test Excel generation with mock data
   - Test email sending with mock SMTP

### Property-Based Tests

Test universal properties across all inputs:

1. **Property Test: Next Execution Calculation**
   - **Property 3: Next Execution Calculation**
   - Generate random frequencies and times
   - Verify next_execution is always in the future
   - Verify next_execution matches frequency pattern

2. **Property Test: Email Validation**
   - **Property 2: Valid Email Format**
   - Generate random email strings
   - Verify validation accepts valid emails
   - Verify validation rejects invalid emails

3. **Property Test: Execution Statistics**
   - **Property 7: Execution History Integrity**
   - Generate random execution histories
   - Verify total = successful + failed always holds

4. **Property Test: Permission Enforcement**
   - **Property 8: Permission Enforcement**
   - Generate random user/report combinations
   - Verify only owner or admin can modify

### Integration Tests

Test complete workflows:

1. **Test: Complete Report Lifecycle**
   - Create report → Execute → Send email → Verify delivery
   - Verify all database records created correctly
   - Verify files generated and saved

2. **Test: Celery Task Execution**
   - Trigger task → Wait for completion → Verify results
   - Test retry mechanism with forced failures
   - Test cleanup task removes old files

3. **Test: AJAX Workflow**
   - Create via AJAX → Verify in database
   - Update via AJAX → Verify changes
   - Delete via AJAX → Verify soft delete

### Test Configuration

- **Framework:** pytest + pytest-django
- **Coverage Target:** 85% minimum
- **Property Test Iterations:** 100 per property
- **Mock Services:** SMTP, File I/O, Celery (for unit tests)
- **Real Services:** Database, Redis (for integration tests)

