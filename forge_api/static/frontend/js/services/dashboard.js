/**
 * Gestor del Dashboard de Servicios
 * Maneja KPIs dinámicos, actualización automática y filtros
 */

class ServiceDashboard {
    constructor(options = {}) {
        this.statsApiUrl = options.statsApiUrl || '/api/services/stats/';
        this.period = options.period || 'today';
        this.dateFrom = options.dateFrom;
        this.dateTo = options.dateTo;
        this.csrfToken = options.csrfToken;
        this.updateInterval = null;
        this.updateIntervalTime = 30000; // 30 segundos
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.startAutoUpdate();
    }
    
    bindEvents() {
        // Eventos ya manejados en el template
    }
    
    startAutoUpdate() {
        // Actualizar KPIs automáticamente cada 30 segundos
        this.updateInterval = setInterval(() => {
            this.refreshKPIs();
        }, this.updateIntervalTime);
    }
    
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    async refreshKPIs() {
        const loadingElement = document.getElementById('loading-kpis');
        const kpiContainer = document.getElementById('kpi-container');
        
        // Mostrar loading
        if (loadingElement) {
            loadingElement.classList.add('show');
        }
        if (kpiContainer) {
            kpiContainer.style.opacity = '0.5';
        }
        
        try {
            // Parámetros para la API
            const params = {
                period: this.period
            };
            
            if (this.dateFrom && this.dateTo) {
                params.start_date = this.dateFrom;
                params.end_date = this.dateTo;
            }
            
            const queryString = new URLSearchParams(params).toString();
            const response = await fetch(`${this.statsApiUrl}?${queryString}`, {
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Actualizar KPIs
            this.updateKPIDisplay(data);
            
        } catch (error) {
            console.error('Error refreshing KPIs:', error);
            // No mostrar error al usuario para actualizaciones automáticas
        } finally {
            // Ocultar loading
            if (loadingElement) {
                loadingElement.classList.remove('show');
            }
            if (kpiContainer) {
                kpiContainer.style.opacity = '1';
            }
        }
    }
    
    updateKPIDisplay(data) {
        // Actualizar cada KPI individualmente
        const kpis = {
            'kpi-active-orders': data.work_order_stats?.total_active || 0,
            'kpi-completed-today': data.work_order_stats?.completed_today || 0,
            'kpi-completed-period': data.work_order_stats?.completed_period || 0,
            'kpi-revenue': `$${parseFloat(data.service_metrics?.total_revenue || 0).toFixed(2)}`,
            'kpi-avg-time': `${parseFloat(data.service_metrics?.avg_completion_time || 0).toFixed(1)}d`,
            'kpi-active-techs': data.active_technicians_count || 0
        };
        
        // Animar cambios en los valores
        Object.entries(kpis).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                const oldValue = element.textContent.trim();
                if (oldValue !== String(value)) {
                    // Animación de cambio
                    element.style.transform = 'scale(1.2)';
                    element.textContent = value;
                    
                    setTimeout(() => {
                        element.style.transform = 'scale(1)';
                    }, 300);
                }
            }
        });
    }
}

// Instancia global
window.ServiceDashboard = {
    instance: null,
    
    init: function(options) {
        this.instance = new ServiceDashboard(options);
        return this.instance;
    },
    
    refreshKPIs: function() {
        if (this.instance) {
            this.instance.refreshKPIs();
        }
    },
    
    stopAutoUpdate: function() {
        if (this.instance) {
            this.instance.stopAutoUpdate();
        }
    }
};
