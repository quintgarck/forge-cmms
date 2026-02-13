/**
 * ForgeDB Dashboard Charts
 * 
 * Interactive charts and visualizations for the dashboard using Chart.js
 * with advanced features like drill-down, filtering, and real-time updates.
 */

class DashboardCharts {
    constructor() {
        this.charts = new Map();
        this.chartConfigs = new Map();
        this.colors = {
            primary: '#0d6efd',
            secondary: '#6c757d',
            success: '#198754',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#0dcaf0',
            light: '#f8f9fa',
            dark: '#212529'
        };
        
        this.init();
    }
    
    init() {
        // Set Chart.js global defaults
        Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#6c757d';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.padding = 20;
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        Chart.defaults.plugins.tooltip.titleColor = '#fff';
        Chart.defaults.plugins.tooltip.bodyColor = '#fff';
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
        Chart.defaults.plugins.tooltip.padding = 12;
        
        this.initializeCharts();
    }
    
    initializeCharts() {
        // Initialize all dashboard charts
        this.createWorkOrdersChart();
        this.createStatusDistributionChart();
        this.createRevenueChart();
        this.createProductivityChart();
        this.createInventoryChart();
    }
    
    createWorkOrdersChart() {
        const ctx = document.getElementById('workordersChart');
        if (!ctx) return;
        
        const config = {
            type: 'bar',
            data: {
                labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
                datasets: [{
                    label: 'Órdenes Creadas',
                    data: [12, 19, 8, 15, 22, 8, 5],
                    backgroundColor: this.colors.primary,
                    borderColor: this.colors.primary,
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false,
                }, {
                    label: 'Órdenes Completadas',
                    data: [8, 15, 6, 12, 18, 6, 3],
                    backgroundColor: this.colors.success,
                    borderColor: this.colors.success,
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            boxWidth: 12,
                            boxHeight: 12,
                        }
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return `${context[0].label}`;
                            },
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y}`;
                            },
                            afterBody: function(context) {
                                const created = context.find(c => c.datasetIndex === 0)?.parsed.y || 0;
                                const completed = context.find(c => c.datasetIndex === 1)?.parsed.y || 0;
                                const efficiency = created > 0 ? Math.round((completed / created) * 100) : 0;
                                return [`Eficiencia: ${efficiency}%`];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                weight: '500'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                return Number.isInteger(value) ? value : '';
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const element = elements[0];
                        const label = this.charts.get('workorders').data.labels[element.index];
                        this.handleChartClick('workorders', label, element);
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, config);
        this.charts.set('workorders', chart);
        this.chartConfigs.set('workorders', config);
        
        // Store reference globally for external access
        window.workordersChart = chart;
    }
    
    createStatusDistributionChart() {
        const ctx = document.getElementById('statusChart');
        if (!ctx) return;
        
        const config = {
            type: 'doughnut',
            data: {
                labels: ['Pendientes', 'En Progreso', 'Completadas', 'Canceladas'],
                datasets: [{
                    data: [30, 45, 20, 5],
                    backgroundColor: [
                        this.colors.warning,
                        this.colors.info,
                        this.colors.success,
                        this.colors.danger
                    ],
                    borderWidth: 0,
                    cutout: '65%',
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const element = elements[0];
                        const label = this.charts.get('status').data.labels[element.index];
                        this.handleChartClick('status', label, element);
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, config);
        this.charts.set('status', chart);
        this.chartConfigs.set('status', config);
        
        // Store reference globally for external access
        window.statusChart = chart;
    }
    
    createRevenueChart() {
        const ctx = document.getElementById('revenueChart');
        if (!ctx) return;
        
        const config = {
            type: 'line',
            data: {
                labels: Array.from({length: 30}, (_, i) => {
                    const date = new Date();
                    date.setDate(date.getDate() - (29 - i));
                    return i % 5 === 0 ? date.toLocaleDateString('es-MX', {month: 'short', day: 'numeric'}) : '';
                }),
                datasets: [{
                    label: 'Ingresos Diarios',
                    data: Array.from({length: 30}, () => Math.floor(Math.random() * 50000) + 10000),
                    borderColor: this.colors.success,
                    backgroundColor: this.colors.success + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: this.colors.success,
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return `Día ${context[0].dataIndex + 1}`;
                            },
                            label: function(context) {
                                return `Ingresos: $${context.parsed.y.toLocaleString('es-MX')}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + (value / 1000).toFixed(0) + 'K';
                            }
                        }
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, config);
        this.charts.set('revenue', chart);
        this.chartConfigs.set('revenue', config);
        
        // Store reference globally for external access
        window.revenueChart = chart;
    }
    
    createProductivityChart() {
        const ctx = document.getElementById('productivityChart');
        if (!ctx) return;
        
        const config = {
            type: 'radar',
            data: {
                labels: ['Velocidad', 'Calidad', 'Eficiencia', 'Satisfacción', 'Innovación', 'Colaboración'],
                datasets: [{
                    label: 'Este Mes',
                    data: [85, 92, 78, 88, 75, 90],
                    borderColor: this.colors.primary,
                    backgroundColor: this.colors.primary + '20',
                    borderWidth: 2,
                    pointBackgroundColor: this.colors.primary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }, {
                    label: 'Mes Anterior',
                    data: [78, 85, 82, 85, 70, 85],
                    borderColor: this.colors.secondary,
                    backgroundColor: this.colors.secondary + '10',
                    borderWidth: 2,
                    pointBackgroundColor: this.colors.secondary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        angleLines: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        pointLabels: {
                            font: {
                                size: 11,
                                weight: '500'
                            }
                        },
                        ticks: {
                            display: false
                        }
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, config);
        this.charts.set('productivity', chart);
        this.chartConfigs.set('productivity', config);
    }
    
    createInventoryChart() {
        const ctx = document.getElementById('inventoryChart');
        if (!ctx) return;
        
        const config = {
            type: 'bar',
            data: {
                labels: ['Almacén A', 'Almacén B', 'Almacén C', 'Almacén D'],
                datasets: [{
                    label: 'Stock Normal',
                    data: [120, 85, 95, 110],
                    backgroundColor: this.colors.success,
                    borderRadius: 4,
                    borderSkipped: false,
                }, {
                    label: 'Stock Bajo',
                    data: [15, 25, 8, 12],
                    backgroundColor: this.colors.warning,
                    borderRadius: 4,
                    borderSkipped: false,
                }, {
                    label: 'Stock Crítico',
                    data: [3, 8, 2, 5],
                    backgroundColor: this.colors.danger,
                    borderRadius: 4,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end'
                    },
                    tooltip: {
                        callbacks: {
                            afterBody: function(context) {
                                const total = context.reduce((sum, item) => sum + item.parsed.y, 0);
                                return [`Total: ${total} productos`];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            }
        };
        
        const chart = new Chart(ctx, config);
        this.charts.set('inventory', chart);
        this.chartConfigs.set('inventory', config);
    }
    
    // Chart interaction handlers
    handleChartClick(chartType, label, element) {
        console.log(`Chart clicked: ${chartType}, Label: ${label}`, element);
        
        // Show detailed modal or navigate to filtered view
        switch (chartType) {
            case 'workorders':
                this.showWorkOrderDetails(label);
                break;
            case 'status':
                this.showStatusDetails(label);
                break;
            default:
                console.log(`No handler for chart type: ${chartType}`);
        }
    }
    
    showWorkOrderDetails(day) {
        // Create and show modal with work order details for the selected day
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Órdenes de Trabajo - ${day}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Detalles de las órdenes de trabajo para ${day}</p>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Cliente</th>
                                        <th>Estado</th>
                                        <th>Técnico</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>#1001</td>
                                        <td>Cliente A</td>
                                        <td><span class="badge bg-warning">Pendiente</span></td>
                                        <td>Juan Pérez</td>
                                    </tr>
                                    <tr>
                                        <td>#1002</td>
                                        <td>Cliente B</td>
                                        <td><span class="badge bg-success">Completada</span></td>
                                        <td>María García</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        <a href="/workorders/" class="btn btn-primary">Ver Todas</a>
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
        
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }
    
    showStatusDetails(status) {
        // Navigate to work orders filtered by status
        const statusMap = {
            'Pendientes': 'pending',
            'En Progreso': 'in_progress',
            'Completadas': 'completed',
            'Canceladas': 'cancelled'
        };
        
        const statusCode = statusMap[status] || status.toLowerCase();
        window.location.href = `/workorders/?status=${statusCode}`;
    }
    
    // Data update methods
    updateChart(chartName, newData) {
        const chart = this.charts.get(chartName);
        if (!chart) {
            console.warn(`Chart '${chartName}' not found`);
            return;
        }
        
        // Update chart data
        if (newData.labels) {
            chart.data.labels = newData.labels;
        }
        
        if (newData.datasets) {
            newData.datasets.forEach((dataset, index) => {
                if (chart.data.datasets[index]) {
                    Object.assign(chart.data.datasets[index], dataset);
                }
            });
        }
        
        // Animate the update
        chart.update('active');
    }
    
    updateAllCharts(dashboardData) {
        if (!dashboardData.charts) return;
        
        // Update work orders chart
        if (dashboardData.charts.workorders_week) {
            this.updateChart('workorders', {
                labels: dashboardData.charts.workorders_week.labels,
                datasets: [
                    { data: dashboardData.charts.workorders_week.created },
                    { data: dashboardData.charts.workorders_week.completed }
                ]
            });
        }
        
        // Update status chart
        if (dashboardData.charts.status_distribution) {
            this.updateChart('status', {
                labels: dashboardData.charts.status_distribution.labels,
                datasets: [
                    { data: dashboardData.charts.status_distribution.data }
                ]
            });
        }
        
        // Update revenue chart
        if (dashboardData.charts.revenue_trend) {
            this.updateChart('revenue', {
                labels: dashboardData.charts.revenue_trend.labels,
                datasets: [
                    { data: dashboardData.charts.revenue_trend.data }
                ]
            });
        }
    }
    
    // Utility methods
    resizeCharts() {
        this.charts.forEach(chart => {
            chart.resize();
        });
    }
    
    destroyChart(chartName) {
        const chart = this.charts.get(chartName);
        if (chart) {
            chart.destroy();
            this.charts.delete(chartName);
            this.chartConfigs.delete(chartName);
        }
    }
    
    destroyAllCharts() {
        this.charts.forEach((chart, name) => {
            chart.destroy();
        });
        this.charts.clear();
        this.chartConfigs.clear();
    }
    
    // Export functionality
    exportChart(chartName, format = 'png') {
        const chart = this.charts.get(chartName);
        if (!chart) {
            console.warn(`Chart '${chartName}' not found`);
            return;
        }
        
        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = `${chartName}-chart.${format}`;
        link.href = url;
        link.click();
    }
    
    exportAllCharts() {
        this.charts.forEach((chart, name) => {
            this.exportChart(name);
        });
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.body.classList.contains('dashboard-page')) {
        window.dashboardCharts = new DashboardCharts();
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.dashboardCharts) {
                window.dashboardCharts.resizeCharts();
            }
        });
    }
});

// Export for global use
window.DashboardCharts = DashboardCharts;