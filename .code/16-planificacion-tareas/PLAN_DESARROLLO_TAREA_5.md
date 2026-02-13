# Plan de Desarrollo Detallado - Tarea 5: Dashboard de Servicios Avanzado
**Fecha**: 15 de enero de 2026  
**Tarea**: Implementar dashboard completo de servicios con KPIs, gráficos y análisis

---

## 🎯 Objetivo General

Crear un dashboard completo de servicios que permita a los gerentes y administradores monitorear, analizar y gestionar eficientemente todas las operaciones de servicio del taller automotriz.

---

## 📊 Estado Actual vs Objetivo

### Estado Actual
- ✅ CRUDs de Catalog completos (Tarea 4)
- ✅ API backend funcionando
- ✅ Sistema de servicios básico existente
- ⏳ Dashboard de servicios básico (sin KPIs avanzados)

### Objetivo Final
- ✅ Dashboard con KPIs en tiempo real
- ✅ Gráficos interactivos (Chart.js)
- ✅ Sistema de alertas automáticas
- ✅ Análisis de tendencias y comparaciones
- ✅ Reportes exportables en múltiples formatos

---

## 📋 Desglose Detallado de Subtareas

### Subtarea 5.1: Crear Dashboard Principal
**Prioridad**: 🔴 Alta  
**Duración**: 2-3 días  
**Complejidad**: Media

#### Objetivos Específicos
1. Crear vista principal del dashboard con layout responsive
2. Implementar widgets de KPIs dinámicos que se actualicen en tiempo real
3. Agregar selector de rango de fechas con filtrado automático
4. Crear sistema de actualización automática de datos (AJAX polling cada 30 seg)

#### Tareas Técnicas Detalladas

**5.1.1 Vista Django**
```python
# forge_api/frontend/views/service_advanced_views.py
- ServiceDashboardView (LoginRequiredMixin, APIClientMixin, TemplateView)
  - get_context_data(): Cargar KPIs iniciales
  - Método para obtener estadísticas del período
  - Manejo de filtros de fecha
```

**5.1.2 API Client**
```python
# forge_api/frontend/services/api_client.py
- get_service_stats(period='today', start_date=None, end_date=None)
- get_service_kpis()
- get_service_summary()
```

**5.1.3 Template HTML**
```html
<!-- forge_api/templates/frontend/services/service_dashboard.html -->
- Layout con grid Bootstrap 5
- Widgets de KPIs (4-6 widgets principales)
- Selector de rango de fechas
- Área para gráficos (placeholder)
- Panel de alertas (placeholder)
```

**5.1.4 JavaScript**
```javascript
// forge_api/static/frontend/js/services/dashboard.js
- Función de actualización automática (setInterval)
- Función de actualización de KPIs (AJAX)
- Manejo de filtros de fecha
- Loading states
```

**5.1.5 KPIs a Implementar**
1. **Órdenes Activas**: Total de órdenes en progreso
2. **Completadas Hoy**: Contador de órdenes completadas hoy
3. **Ingresos del Período**: Suma de facturas del período
4. **Promedio de Tiempo**: Tiempo promedio por orden
5. **Técnicos Activos**: Número de técnicos trabajando
6. **Tasa de Completación**: % de órdenes completadas vs programadas

**5.1.6 URLs**
```python
# forge_api/frontend/urls.py
path('services/dashboard/', service_advanced_views.ServiceDashboardView.as_view(), name='service_dashboard'),
path('api/services/stats/', service_advanced_views.ServiceStatsAPIView.as_view(), name='service_stats_api'),
```

**5.1.7 Criterios de Aceptación**
- [ ] Dashboard carga en menos de 2 segundos
- [ ] KPIs se actualizan automáticamente cada 30 seg
- [ ] Filtros de fecha funcionan correctamente
- [ ] Layout responsive en móvil, tablet y desktop
- [ ] Loading states claros durante actualización

---

### Subtarea 5.2: Desarrollar Visualizaciones Interactivas
**Prioridad**: 🔴 Alta  
**Duración**: 3-4 días  
**Complejidad**: Media-Alta

#### Objetivos Específicos
1. Implementar gráficos interactivos usando Chart.js
2. Crear múltiples tipos de gráficos (bar, line, pie, donut)
3. Agregar filtros interactivos que actualicen gráficos
4. Implementar tooltips informativos y exportación de gráficos

#### Tareas Técnicas Detalladas

**5.2.1 Gráficos a Implementar**

**Gráfico 1: Productividad por Técnico**
- **Tipo**: Bar Chart Horizontal
- **Datos**: Órdenes completadas por técnico en el período
- **Color**: Gradiente azul
- **Interactividad**: Click para ver detalle del técnico

**Gráfico 2: Servicios por Categoría**
- **Tipo**: Pie/Donut Chart
- **Datos**: Distribución de servicios por categoría
- **Colores**: Paleta diferenciada
- **Interactividad**: Hover muestra porcentaje y cantidad

**Gráfico 3: Tendencias Temporales**
- **Tipo**: Line Chart con múltiples series
- **Datos**: Órdenes completadas, ingresos, tiempo promedio por día/semana
- **Series**: 3 líneas (completadas, ingresos, tiempo)
- **Interactividad**: Zoom y pan en períodos

**Gráfico 4: Comparación Períodos**
- **Tipo**: Bar Chart Agrupado
- **Datos**: Comparar período actual vs anterior
- **Métricas**: Completadas, Ingresos, Tiempo promedio
- **Interactividad**: Toggle entre métricas

**5.2.2 Implementación Chart.js**

**Instalación/Servicio**:
```html
<!-- CDN o archivo local -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
```

**Estructura JavaScript**:
```javascript
// forge_api/static/frontend/js/services/dashboard-charts.js
- ServiceDashboardCharts (clase)
  - init(): Inicializar todos los gráficos
  - updateProductivityChart(data)
  - updateServicesByCategoryChart(data)
  - updateTrendsChart(data)
  - updateComparisonChart(data)
  - updateAllCharts(): Actualizar todos con nuevos datos
  - exportChart(chartId, format='png'): Exportar gráfico
```

**5.2.3 API Endpoints para Datos**

```python
# forge_api/frontend/views/service_advanced_views.py
- ServiceProductivityAPIView (JSONResponse)
  - Retorna: {technicians: [{name, orders_completed, avg_time}]}
  
- ServiceCategoriesAPIView (JSONResponse)
  - Retorna: {categories: [{name, count, percentage}]}
  
- ServiceTrendsAPIView (JSONResponse)
  - Params: period, granularity (day/week/month)
  - Retorna: {dates: [], series: {completed, revenue, avg_time}}
  
- ServiceComparisonAPIView (JSONResponse)
  - Retorna: {current: {...}, previous: {...}}
```

**5.2.4 Template HTML para Gráficos**

```html
<!-- Sección de gráficos en service_dashboard.html -->
<div class="charts-section">
  <!-- Gráfico 1: Productividad -->
  <div class="chart-container">
    <canvas id="productivityChart"></canvas>
  </div>
  
  <!-- Gráfico 2: Servicios por Categoría -->
  <div class="chart-container">
    <canvas id="servicesCategoryChart"></canvas>
  </div>
  
  <!-- Gráfico 3: Tendencias -->
  <div class="chart-container">
    <canvas id="trendsChart"></canvas>
  </div>
  
  <!-- Gráfico 4: Comparación -->
  <div class="chart-container">
    <canvas id="comparisonChart"></canvas>
  </div>
</div>
```

**5.2.5 Filtros Interactivos**

```html
<!-- Filtros para gráficos -->
<div class="chart-filters">
  <select id="chartPeriod" class="form-select">
    <option value="today">Hoy</option>
    <option value="week">Esta Semana</option>
    <option value="month">Este Mes</option>
    <option value="custom">Personalizado</option>
  </select>
  
  <button id="refreshCharts" class="btn btn-primary">
    Actualizar Gráficos
  </button>
  
  <div class="chart-export-buttons">
    <button onclick="exportChart('productivityChart', 'png')">Exportar PNG</button>
    <button onclick="exportChart('productivityChart', 'pdf')">Exportar PDF</button>
  </div>
</div>
```

**5.2.6 Criterios de Aceptación**
- [ ] Todos los gráficos se renderizan correctamente
- [ ] Datos se actualizan al cambiar filtros
- [ ] Tooltips muestran información útil
- [ ] Gráficos son responsive (se adaptan al tamaño)
- [ ] Exportación funciona (PNG, PDF)
- [ ] Performance: Gráficos se cargan en menos de 1 seg

---

### Subtarea 5.3: Implementar Sistema de Alertas
**Prioridad**: 🟡 Media  
**Duración**: 2-3 días  
**Complejidad**: Media

#### Objetivos Específicos
1. Crear panel de alertas activas en tiempo real
2. Desarrollar sistema de configuración de umbrales
3. Implementar notificaciones automáticas
4. Agregar sistema de escalamiento de alertas

#### Tareas Técnicas Detalladas

**5.3.1 Tipos de Alertas**

1. **Órdenes Retrasadas**
   - Condición: Orden programada que excede tiempo estimado + 20%
   - Severidad: Crítica (Rojo)
   - Acción: Enviar notificación al técnico y supervisor

2. **Stock Bajo**
   - Condición: Producto crítico bajo nivel mínimo
   - Severidad: Advertencia (Amarillo)
   - Acción: Notificar a inventario

3. **Técnicos Sobrecargados**
   - Condición: Técnico con >5 órdenes activas
   - Severidad: Advertencia (Amarillo)
   - Acción: Sugerir redistribución

4. **Servicios Anómalos**
   - Condición: Tiempo real > tiempo estimado * 2
   - Severidad: Info (Azul)
   - Acción: Registrar para análisis

5. **Alta Productividad**
   - Condición: Técnico completa >3 órdenes en un día
   - Severidad: Info (Verde)
   - Acción: Reconocimiento

**5.3.2 Implementación Backend**

```python
# forge_api/frontend/services/alert_service.py (nuevo)
class ServiceAlertService:
    def get_active_alerts(self):
        """Obtener alertas activas"""
        
    def check_delayed_orders(self):
        """Verificar órdenes retrasadas"""
        
    def check_low_stock(self):
        """Verificar stock bajo"""
        
    def check_overloaded_technicians(self):
        """Verificar técnicos sobrecargados"""
        
    def create_alert(self, alert_type, severity, message, action_url):
        """Crear nueva alerta"""
```

**5.3.3 Vista de Alertas**

```python
# forge_api/frontend/views/service_advanced_views.py
- ServiceAlertsAPIView (JSONResponse)
  - Retorna: {alerts: [{id, type, severity, message, timestamp, action_url}]}
  
- ServiceAlertsListView (TemplateView)
  - Vista completa de todas las alertas
  - Filtros por tipo y severidad
```

**5.3.4 Template de Alertas**

```html
<!-- Panel de alertas en dashboard -->
<div class="alerts-panel">
  <h5>Alertas Activas</h5>
  <div id="alertsContainer">
    <!-- Alertas dinámicas -->
    <div class="alert alert-danger">
      <strong>Crítica:</strong> Orden #1234 retrasada 2 horas
      <a href="/workorders/1234/">Ver Orden</a>
    </div>
  </div>
</div>
```

**5.3.5 Configuración de Umbrales**

```html
<!-- Modal de configuración -->
<div class="alert-settings">
  <h6>Configuración de Alertas</h6>
  <label>Tiempo máximo de retraso (minutos):</label>
  <input type="number" id="maxDelayMinutes" value="120">
  
  <label>Máximo de órdenes por técnico:</label>
  <input type="number" id="maxOrdersPerTechnician" value="5">
</div>
```

**5.3.6 Criterios de Aceptación**
- [ ] Alertas se generan automáticamente
- [ ] Panel de alertas se actualiza en tiempo real
- [ ] Alertas se pueden filtrar y clasificar
- [ ] Notificaciones se envían correctamente
- [ ] Configuración de umbrales funciona
- [ ] Alertas históricas se guardan

---

### Subtarea 5.4: Agregar Análisis y Reportes
**Prioridad**: 🟡 Media  
**Duración**: 3-4 días  
**Complejidad**: Media-Alta

#### Objetivos Específicos
1. Implementar análisis de tendencias automático
2. Crear reportes automáticos con insights
3. Desarrollar comparaciones históricas
4. Agregar exportación en múltiples formatos (PDF, Excel, CSV)

#### Tareas Técnicas Detalladas

**5.4.1 Análisis de Tendencias**

```python
# forge_api/frontend/services/trend_analyzer.py (nuevo)
class TrendAnalyzer:
    def analyze_productivity_trend(self, period):
        """Analizar tendencia de productividad"""
        
    def analyze_revenue_trend(self, period):
        """Analizar tendencia de ingresos"""
        
    def generate_insights(self, period):
        """Generar insights automáticos"""
        # Ejemplo: "La productividad aumentó 15% esta semana"
```

**5.4.2 Reportes Automáticos**

**Reporte Diario**:
- Resumen del día
- Órdenes completadas
- Ingresos del día
- Técnicos destacados

**Reporte Semanal**:
- Análisis semanal completo
- Comparación con semana anterior
- Tendencias detectadas
- Recomendaciones

**Reporte Mensual**:
- Resumen ejecutivo
- Métricas clave del mes
- Análisis de tendencias
- Proyecciones

**5.4.3 Generación de Reportes**

```python
# forge_api/frontend/views/service_advanced_views.py
- ServiceReportGenerateView (View)
  - Params: report_type, period, format
  - Retorna: PDF, Excel, o CSV según formato
  
- ServiceInsightsAPIView (JSONResponse)
  - Retorna: {insights: [{type, message, impact}]}
```

**5.4.4 Exportación PDF (ReportLab)**

```python
# forge_api/frontend/utils/report_generator.py (nuevo)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

class PDFReportGenerator:
    def generate_service_report(self, data, period):
        """Generar reporte PDF"""
```

**5.4.5 Exportación Excel (openpyxl)**

```python
# forge_api/frontend/utils/excel_generator.py (nuevo)
from openpyxl import Workbook

class ExcelReportGenerator:
    def generate_service_report(self, data, period):
        """Generar reporte Excel con gráficos"""
```

**5.4.6 Comparaciones Históricas**

```python
# Vista de comparación
- ServiceComparisonView (TemplateView)
  - Comparar período actual vs anterior
  - Mostrar diferencias porcentuales
  - Gráficos comparativos
```

**5.4.7 Criterios de Aceptación**
- [ ] Análisis de tendencias funciona correctamente
- [ ] Reportes se generan en todos los formatos
- [ ] Insights son relevantes y precisos
- [ ] Comparaciones históricas son claras
- [ ] Exportación incluye gráficos (PDF, Excel)
- [ ] Reportes se generan en menos de 5 segundos

---

## 📅 Cronograma de Desarrollo

### Semana 1 (Días 1-5)
**Objetivo**: Dashboard Principal Funcional

- **Día 1**: Setup y estructura inicial
  - Crear vistas base
  - Configurar URLs
  - Crear template base

- **Día 2**: Implementar KPIs
  - Crear widgets de KPIs
  - Integrar con API
  - Implementar actualización automática

- **Día 3**: Filtros y ajustes
  - Selector de fechas
  - Filtrado de datos
  - Refinamiento UI

### Semana 2 (Días 6-10)
**Objetivo**: Visualizaciones Completas

- **Día 4-5**: Gráfico Productividad y Categorías
  - Implementar Chart.js
  - Gráfico de productividad
  - Gráfico de categorías

- **Día 6-7**: Gráfico Tendencias y Comparación
  - Gráfico de tendencias
  - Gráfico comparativo
  - Filtros interactivos

- **Día 8-9**: Exportación y refinamiento
  - Exportar gráficos
  - Optimización de performance
  - Testing visual

### Semana 3 (Días 11-15)
**Objetivo**: Alertas y Reportes

- **Día 10-11**: Sistema de Alertas
  - Implementar detección
  - Panel de alertas
  - Configuración de umbrales

- **Día 12-13**: Reportes Básicos
  - Análisis de tendencias
  - Generación de reportes PDF
  - Exportación Excel

- **Día 14-15**: Comparaciones y Finalización
  - Comparaciones históricas
  - Refinamiento final
  - Testing completo

---

## 🔧 Tecnologías y Dependencias

### Frontend
- **Chart.js**: Gráficos interactivos
- **Bootstrap 5**: Layout responsive
- **jQuery/AJAX**: Actualización de datos
- **Date Range Picker**: Selector de fechas

### Backend
- **Django**: Framework web
- **Django REST Framework**: API endpoints
- **ReportLab**: Generación de PDFs
- **openpyxl**: Generación de Excel

### APIs Necesarias
- `/api/services/stats/` - Estadísticas generales
- `/api/services/kpis/` - KPIs del dashboard
- `/api/services/productivity/` - Datos de productividad
- `/api/services/categories/` - Datos por categoría
- `/api/services/trends/` - Datos de tendencias
- `/api/services/alerts/` - Alertas activas
- `/api/services/reports/generate/` - Generar reportes

---

## ✅ Checklist de Verificación

### Subtarea 5.1
- [ ] Dashboard carga correctamente
- [ ] KPIs se muestran correctamente
- [ ] Actualización automática funciona
- [ ] Filtros de fecha funcionan
- [ ] Layout responsive

### Subtarea 5.2
- [ ] Todos los gráficos se renderizan
- [ ] Datos se actualizan correctamente
- [ ] Tooltips funcionan
- [ ] Exportación funciona
- [ ] Performance adecuada

### Subtarea 5.3
- [ ] Alertas se generan automáticamente
- [ ] Panel de alertas funciona
- [ ] Configuración guarda correctamente
- [ ] Notificaciones se envían

### Subtarea 5.4
- [ ] Análisis de tendencias funciona
- [ ] Reportes se generan en todos los formatos
- [ ] Comparaciones son precisas
- [ ] Exportación incluye gráficos

---

## 🎯 Métricas de Éxito

### Performance
- Dashboard carga en < 2 segundos
- Gráficos se renderizan en < 1 segundo
- Actualización automática sin lag perceptible
- Reportes se generan en < 5 segundos

### Funcionalidad
- Todos los KPIs se muestran correctamente
- Todos los gráficos son interactivos
- Alertas se generan en tiempo real
- Reportes son completos y precisos

### UX
- Interfaz intuitiva y fácil de usar
- Feedback visual claro en todas las operaciones
- Responsive en todos los dispositivos
- Accesible (navegación por teclado)

---

**Tarea 5**: 🎯 **Lista para iniciar**  
**Fecha de inicio propuesta**: 15 de enero de 2026  
**Duración total estimada**: 10-14 días
