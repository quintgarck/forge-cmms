/**
 * ForgeDB Dashboard Widgets
 * 
 * Advanced KPI widgets with real-time updates, drill-down capabilities,
 * and interactive visualizations.
 */

class DashboardWidgets {
    constructor() {
        this.widgets = new Map();
        this.updateInterval = null;
        this.isAutoRefreshEnabled = false;
        this.refreshRate = 30000; // 30 seconds
        
        this.init();
    }
    
    init() {
        this.initializeWidgets();
        this.setupEventListeners();
        this.loadInitialData();
    }
    
    initializeWidgets() {
        // KPI Widget configurations
        this.widgetConfigs = {
            workorders: {
                element: '#active-workorders',
                title: 'Órdenes Activas',
                icon: 'clipboard-check',
                color: 'primary',
                format: 'number',
                drillDown: true
            },
            invoices: {
                element: '#pending-invoices',
                title: 'Facturas Pendientes',
                icon: 'receipt',
                color: 'warning',
                format: 'number',
                drillDown: true
            },
            inventory: {
                element: '#low-stock-items',
                title: 'Stock Bajo',
                icon: 'exclamation-triangle',
                color: 'danger',
                format: 'number',
                drillDown: true
            },
            productivity: {
                element: '#technician-productivity',
                title: 'Productividad',
                icon: 'graph-up',
                color: 'success',
                format: 'percentage',
                drillDown: true
            }
        };
        
        // Initialize each widget
        Object.keys(this.widgetConfigs).forEach(key => {
            this.createWidget(key, this.widgetConfigs[key]);
        });
    }
    
    createWidget(widgetId, config) {
        const widget = new KPIWidget(widgetId, config);
        this.widgets.set(widgetId, widget);
        return widget;
    }
    
    setupEventListeners() {
        // Auto-refresh toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="toggle-auto-refresh"]')) {
                this.toggleAutoRefresh();
            }
            
            // KPI drill-down
            if (e.target.closest('[data-kpi-drilldown]')) {
                const kpiType = e.target.closest('[data-kpi-drilldown]').dataset.kpiDrilldown;
                this.showKPIDetails(kpiType);
            }
        });
        
        // Refresh button
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="refresh-dashboard"]')) {
                this.refreshAllWidgets();
            }
        });
    }
    
    async loadInitialData() {
        try {
            const data = await ForgeDB.api.get('dashboard/');
            this.updateAllWidgets(data);
        } catch (error) {
            console.error('Failed to load initial dashboard data:', error);
            ForgeDB.utils.showToast('Error al cargar datos del dashboard', 'danger');
        }
    }
    
    updateAllWidgets(data) {
        // Update KPI widgets
        this.widgets.get('workorders')?.update(data.active_work_orders, {
            trend: data.workorders_trend,
            subtitle: `${data.workorders_trend > 0 ? '+' : ''}${data.workorders_trend}% vs ayer`
        });
        
        this.widgets.get('invoices')?.update(data.pending_invoices, {
            trend: data.overdue_invoices > 0 ? 'down' : 'up',
            subtitle: `${data.overdue_invoices} vencidas`
        });
        
        this.widgets.get('inventory')?.update(data.low_stock_items, {
            trend: data.critical_stock > 0 ? 'down' : 'up',
            subtitle: `${data.critical_stock} críticos`
        });
        
        this.widgets.get('productivity')?.update(data.technician_productivity, {
            trend: data.technician_productivity > 75 ? 'up' : 'down',
            subtitle: `${data.avg_completion_days} días promedio`
        });
        
        // Update trend indicators
        this.updateTrendIndicators(data);
        
        // Update charts if they exist
        if (window.dashboardCharts) {
            this.updateCharts(data.charts);
        }
        
        // Update alerts
        this.updateAlerts(data.recent_alerts);
        
        // Update summary stats
        this.updateSummaryStats(data.summary);
    }
    
    updateTrendIndicators(data) {
        const trends = {
            'workorders-trend': data.workorders_trend,
            'invoices-trend': data.revenue_trend,
            'stock-trend': data.critical_stock > 0 ? -10 : 5,
            'productivity-trend': data.technician_productivity - 75
        };
        
        Object.entries(trends).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                const isPositive = value > 0;
                const icon = isPositive ? 'arrow-up' : 'arrow-down';
                const colorClass = isPositive ? 'text-success' : 'text-danger';
                
                element.innerHTML = `
                    <i class="bi bi-${icon} ${colorClass} me-1"></i>
                    <span>${Math.abs(value)}% vs período anterior</span>
                `;
            }
        });
    }
    
    updateCharts(chartData) {
        // Update work orders chart
        if (window.workordersChart && chartData.workorders_week) {
            window.workordersChart.data.labels = chartData.workorders_week.labels;
            window.workordersChart.data.datasets[0].data = chartData.workorders_week.created;
            if (chartData.workorders_week.completed) {
                window.workordersChart.data.datasets[1].data = chartData.workorders_week.completed;
            }
            window.workordersChart.update('none');
        }
        
        // Update status chart
        if (window.statusChart && chartData.status_distribution) {
            window.statusChart.data.labels = chartData.status_distribution.labels;
            window.statusChart.data.datasets[0].data = chartData.status_distribution.data;
            window.statusChart.update('none');
        }
        
        // Update revenue chart if it exists
        if (window.revenueChart && chartData.revenue_trend) {
            window.revenueChart.data.labels = chartData.revenue_trend.labels;
            window.revenueChart.data.datasets[0].data = chartData.revenue_trend.data;
            window.revenueChart.update('none');
        }
    }
    
    updateAlerts(alerts) {
        const alertsContainer = document.getElementById('system-alerts');
        if (!alertsContainer) return;
        
        if (alerts.length === 0) {
            alertsContainer.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-check-circle display-4 text-success opacity-50"></i>
                    <h6 class="mt-3 text-muted">No hay alertas activas</h6>
                    <p class="text-muted small">El sistema está funcionando correctamente</p>
                </div>
            `;
            return;
        }
        
        const alertsHTML = alerts.map(alert => `
            <div class="alert alert-${alert.severity} alert-dismissible fade show mb-2" role="alert">
                <div class="d-flex align-items-start">
                    <div class="flex-shrink-0 me-2">
                        <i class="bi bi-${this.getAlertIcon(alert.severity)}-fill"></i>
                    </div>
                    <div class="flex-grow-1">
                        <strong>${alert.title}</strong>
                        <p class="mb-1">${alert.message}</p>
                        <small class="text-muted">${this.formatDate(alert.created_at)}</small>
                    </div>
                    <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
                </div>
            </div>
        `).join('');
        
        alertsContainer.innerHTML = alertsHTML;
    }
    
    updateSummaryStats(summary) {
        const stats = {
            'total-clients': summary.total_clients,
            'total-equipment': summary.total_equipment,
            'total-products': summary.total_products,
            'total-warehouses': summary.total_warehouses
        };
        
        Object.entries(stats).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = this.formatNumber(value);
            }
        });
    }
    
    async refreshAllWidgets() {
        const refreshBtn = document.querySelector('[data-action="refresh-dashboard"]');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Actualizando...';
        }
        
        try {
            const data = await ForgeDB.api.get('dashboard/');
            this.updateAllWidgets(data);
            ForgeDB.utils.showToast('Dashboard actualizado exitosamente', 'success');
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
            ForgeDB.utils.showToast('Error al actualizar dashboard', 'danger');
        } finally {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Actualizar';
            }
        }
    }
    
    async showKPIDetails(kpiType) {
        try {
            const data = await ForgeDB.api.get(`dashboard/kpi/${kpiType}/`);
            this.displayKPIModal(kpiType, data);
        } catch (error) {
            console.error(`Failed to load KPI details for ${kpiType}:`, error);
            ForgeDB.utils.showToast(`Error al cargar detalles de ${kpiType}`, 'danger');
        }
    }
    
    displayKPIModal(kpiType, data) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Detalles: ${this.getKPITitle(kpiType)}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${this.generateKPIDetailsHTML(kpiType, data.data)}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        <button type="button" class="btn btn-primary" onclick="window.print()">Imprimir</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        if (typeof bootstrap === 'undefined') {
            console.error('Bootstrap is not loaded');
            return;
        }
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Clean up modal after hiding
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }
    
    generateKPIDetailsHTML(kpiType, data) {
        switch (kpiType) {
            case 'workorders':
                return `
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Estado de Órdenes</h6>
                            <ul class="list-group">
                                ${data.by_status.map(item => `
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>${item.status || 'Sin estado'}</span>
                                        <span class="badge bg-primary">${item.count}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Métricas</h6>
                            <p><strong>Total Activas:</strong> ${data.total_active}</p>
                            <p><strong>Vencidas:</strong> ${data.overdue}</p>
                            <p><strong>Esta Semana:</strong> ${data.this_week}</p>
                        </div>
                    </div>
                `;
            case 'invoices':
                return `
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Análisis de Antigüedad</h6>
                            <ul class="list-group">
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>0-30 días</span>
                                    <span class="badge bg-success">${data.aging_analysis['0-30']}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>31-60 días</span>
                                    <span class="badge bg-warning">${data.aging_analysis['31-60']}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <span>60+ días</span>
                                    <span class="badge bg-danger">${data.aging_analysis['60+']}</span>
                                </li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Métricas Financieras</h6>
                            <p><strong>Total Pendientes:</strong> ${data.total_pending}</p>
                            <p><strong>Vencidas:</strong> ${data.overdue}</p>
                            <p><strong>Monto Pendiente:</strong> $${this.formatNumber(data.total_amount_pending)}</p>
                        </div>
                    </div>
                `;
            case 'inventory':
                return `
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Estado del Inventario</h6>
                            <p><strong>Total Productos:</strong> ${data.total_products}</p>
                            <p><strong>Stock Bajo:</strong> ${data.low_stock}</p>
                            <p><strong>Stock Crítico:</strong> ${data.critical_stock}</p>
                            <p><strong>Sin Stock:</strong> ${data.out_of_stock}</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Valor del Inventario</h6>
                            <p><strong>Valor Total:</strong> $${this.formatNumber(data.total_value)}</p>
                            <h6>Por Almacén</h6>
                            <ul class="list-group">
                                ${data.by_warehouse.map(wh => `
                                    <li class="list-group-item d-flex justify-content-between">
                                        <span>${wh.warehouse__name || 'Sin nombre'}</span>
                                        <span class="badge bg-info">${wh.total_items}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                `;
            case 'productivity':
                return `
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Productividad Semanal</h6>
                            <p><strong>Completadas:</strong> ${data.completed_this_week}</p>
                            <p><strong>Total:</strong> ${data.total_this_week}</p>
                            <p><strong>Tasa de Completado:</strong> ${data.completion_rate}%</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Métricas de Eficiencia</h6>
                            <p><strong>Tiempo Promedio:</strong> ${data.avg_completion_time} días</p>
                            <p><em>Más métricas disponibles próximamente</em></p>
                        </div>
                    </div>
                `;
            default:
                return '<p>Detalles no disponibles para este KPI.</p>';
        }
    }
    
    toggleAutoRefresh() {
        if (this.isAutoRefreshEnabled) {
            this.stopAutoRefresh();
        } else {
            this.startAutoRefresh();
        }
    }
    
    startAutoRefresh() {
        this.isAutoRefreshEnabled = true;
        this.updateInterval = setInterval(() => {
            this.refreshAllWidgets();
        }, this.refreshRate);
        
        const toggleBtn = document.querySelector('[data-action="toggle-auto-refresh"]');
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="bi bi-pause-circle me-1"></i>Pausar Auto-actualización';
        }
        
        ForgeDB.utils.showToast('Auto-actualización activada', 'success');
    }
    
    stopAutoRefresh() {
        this.isAutoRefreshEnabled = false;
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        const toggleBtn = document.querySelector('[data-action="toggle-auto-refresh"]');
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i>Activar Auto-actualización';
        }
        
        ForgeDB.utils.showToast('Auto-actualización pausada', 'info');
    }
    
    // Utility methods
    getAlertIcon(severity) {
        const icons = {
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle',
            'success': 'check-circle'
        };
        return icons[severity] || 'info-circle';
    }
    
    getKPITitle(kpiType) {
        const titles = {
            'workorders': 'Órdenes de Trabajo',
            'invoices': 'Facturas',
            'inventory': 'Inventario',
            'productivity': 'Productividad'
        };
        return titles[kpiType] || kpiType;
    }
    
    formatNumber(num) {
        return new Intl.NumberFormat('es-MX').format(num);
    }
    
    formatDate(dateString) {
        if (!dateString) return 'Fecha no disponible';
        return new Date(dateString).toLocaleString('es-MX');
    }
}

/**
 * Individual KPI Widget Class
 */
class KPIWidget {
    constructor(id, config) {
        this.id = id;
        this.config = config;
        this.element = document.querySelector(config.element);
        this.currentValue = 0;
        this.previousValue = 0;
        
        this.setupWidget();
    }
    
    setupWidget() {
        if (!this.element) {
            console.warn(`KPI Widget element not found: ${this.config.element}`);
            return;
        }
        
        // Add drill-down capability
        if (this.config.drillDown) {
            const card = this.element.closest('.card');
            if (card) {
                card.style.cursor = 'pointer';
                card.setAttribute('data-kpi-drilldown', this.id);
                card.setAttribute('title', `Click para ver detalles de ${this.config.title}`);
            }
        }
    }
    
    update(value, options = {}) {
        this.previousValue = this.currentValue;
        this.currentValue = value;
        
        // Animate value change
        this.animateValue(this.previousValue, value);
        
        // Update trend indicator if provided
        if (options.trend !== undefined) {
            this.updateTrend(options.trend);
        }
        
        // Update subtitle if provided
        if (options.subtitle) {
            this.updateSubtitle(options.subtitle);
        }
    }
    
    animateValue(start, end) {
        const duration = 1000; // 1 second
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function (ease-out)
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentValue = start + (end - start) * easeOut;
            
            // Format and display value
            const displayValue = this.config.format === 'percentage' 
                ? Math.round(currentValue) + '%'
                : Math.round(currentValue);
            
            this.element.textContent = displayValue;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    updateTrend(trend) {
        const trendElement = this.element.parentElement.querySelector('.trend-indicator');
        if (!trendElement) return;
        
        let trendClass = 'text-muted';
        let trendIcon = 'dash';
        
        if (typeof trend === 'number') {
            if (trend > 0) {
                trendClass = 'text-success';
                trendIcon = 'arrow-up';
            } else if (trend < 0) {
                trendClass = 'text-danger';
                trendIcon = 'arrow-down';
            }
        } else if (trend === 'up') {
            trendClass = 'text-success';
            trendIcon = 'arrow-up';
        } else if (trend === 'down') {
            trendClass = 'text-danger';
            trendIcon = 'arrow-down';
        }
        
        trendElement.className = `trend-indicator ${trendClass}`;
        trendElement.innerHTML = `<i class="bi bi-${trendIcon}"></i>`;
    }
    
    updateSubtitle(subtitle) {
        const subtitleElement = this.element.parentElement.querySelector('.widget-subtitle');
        if (subtitleElement) {
            subtitleElement.textContent = subtitle;
        }
    }
}

// Initialize dashboard widgets when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.body.classList.contains('dashboard-page')) {
        window.dashboardWidgets = new DashboardWidgets();
    }
});

// Export for global use
window.DashboardWidgets = DashboardWidgets;
window.KPIWidget = KPIWidget;