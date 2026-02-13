/**
 * Gestor de Gráficos del Dashboard de Servicios
 * Utiliza Chart.js para visualizaciones interactivas
 */

class ServiceDashboardCharts {
    constructor(options = {}) {
        this.productivityUrl = options.productivityUrl || '/api/services/productivity/';
        this.categoriesUrl = options.categoriesUrl || '/api/services/categories/';
        this.trendsUrl = options.trendsUrl || '/api/services/trends/';
        this.comparisonUrl = options.comparisonUrl || '/api/services/comparison/';
        this.csrfToken = options.csrfToken;
        this.period = options.period || 'month';
        this.dateFrom = options.dateFrom;
        this.dateTo = options.dateTo;
        
        // Instancias de gráficos
        this.charts = {
            productivity: null,
            categories: null,
            trends: null,
            comparison: null
        };
        
        this.init();
    }
    
    init() {
        this.initProductivityChart();
        this.initCategoriesChart();
        this.initTrendsChart();
        this.initComparisonChart();
        
        // Cargar datos iniciales
        this.loadAllCharts();
    }
    
    async loadAllCharts() {
        await Promise.all([
            this.loadProductivityChart(),
            this.loadCategoriesChart(),
            this.loadTrendsChart(),
            this.loadComparisonChart()
        ]);
    }
    
    // ========== Gráfico 1: Productividad por Técnico ==========
    initProductivityChart() {
        const ctx = document.getElementById('productivityChart');
        if (!ctx) return;
        
        this.charts.productivity = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Órdenes Completadas',
                    data: [],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y', // Horizontal bar chart
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                const index = context.dataIndex;
                                const tech = this.productivityData?.technicians?.[index];
                                if (tech) {
                                    return [
                                        `Horas totales: ${tech.total_hours}h`,
                                        `Tiempo promedio: ${tech.avg_time}h`
                                    ];
                                }
                                return '';
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Productividad por Técnico'
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Órdenes Completadas'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Técnicos'
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const tech = this.productivityData?.technicians?.[index];
                        if (tech) {
                            // TODO: Navegar a detalle del técnico
                            console.log('Técnico seleccionado:', tech);
                        }
                    }
                }
            }
        });
    }
    
    async loadProductivityChart() {
        try {
            const data = await this.fetchData(this.productivityUrl);
            this.productivityData = data;
            
            if (this.charts.productivity && data.technicians) {
                this.charts.productivity.data.labels = data.technicians.map(t => t.name);
                this.charts.productivity.data.datasets[0].data = data.technicians.map(t => t.orders_completed);
                this.charts.productivity.update();
            }
        } catch (error) {
            console.error('Error loading productivity chart:', error);
        }
    }
    
    // ========== Gráfico 2: Servicios por Categoría ==========
    initCategoriesChart() {
        const ctx = document.getElementById('servicesCategoryChart');
        if (!ctx) return;
        
        this.charts.categories = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(153, 102, 255, 0.8)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Distribución por Tipo de Servicio'
                    }
                }
            }
        });
    }
    
    async loadCategoriesChart() {
        try {
            const data = await this.fetchData(this.categoriesUrl);
            
            if (this.charts.categories && data.categories) {
                this.charts.categories.data.labels = data.categories.map(c => c.name);
                this.charts.categories.data.datasets[0].data = data.categories.map(c => c.count);
                this.charts.categories.update();
            }
        } catch (error) {
            console.error('Error loading categories chart:', error);
        }
    }
    
    // ========== Gráfico 3: Tendencias Temporales ==========
    initTrendsChart() {
        const ctx = document.getElementById('trendsChart');
        if (!ctx) return;
        
        this.charts.trends = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Órdenes Completadas',
                        data: [],
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Ingresos',
                        data: [],
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    },
                    {
                        label: 'Tiempo Promedio (horas)',
                        data: [],
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    title: {
                        display: true,
                        text: 'Tendencias Temporales'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Período'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Cantidad / Horas'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Ingresos ($)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
    
    async loadTrendsChart() {
        try {
            const params = new URLSearchParams({
                period: this.period,
                granularity: 'day'
            });
            if (this.dateFrom) params.append('start_date', this.dateFrom);
            if (this.dateTo) params.append('end_date', this.dateTo);
            
            const data = await this.fetchData(`${this.trendsUrl}?${params.toString()}`);
            
            if (this.charts.trends && data.dates && data.series) {
                // Formatear fechas para mostrar
                const formattedDates = data.dates.map(date => {
                    try {
                        const d = new Date(date);
                        return d.toLocaleDateString('es-ES', { 
                            month: 'short', 
                            day: 'numeric' 
                        });
                    } catch {
                        return date;
                    }
                });
                
                this.charts.trends.data.labels = formattedDates;
                this.charts.trends.data.datasets[0].data = data.series.completed || [];
                this.charts.trends.data.datasets[1].data = data.series.revenue || [];
                this.charts.trends.data.datasets[2].data = data.series.avg_time || [];
                this.charts.trends.update();
            }
        } catch (error) {
            console.error('Error loading trends chart:', error);
        }
    }
    
    // ========== Gráfico 4: Comparación de Períodos ==========
    initComparisonChart() {
        const ctx = document.getElementById('comparisonChart');
        if (!ctx) return;
        
        this.charts.comparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Órdenes Completadas', 'Ingresos ($)', 'Tiempo Promedio (h)'],
                datasets: [
                    {
                        label: 'Período Actual',
                        data: [],
                        backgroundColor: 'rgba(54, 162, 235, 0.8)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Período Anterior',
                        data: [],
                        backgroundColor: 'rgba(255, 99, 132, 0.8)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                if (this.comparisonData?.changes) {
                                    const index = context.dataIndex;
                                    const changes = this.comparisonData.changes;
                                    let changeValue = 0;
                                    
                                    if (index === 0) changeValue = changes.completed;
                                    else if (index === 1) changeValue = changes.revenue;
                                    else if (index === 2) changeValue = changes.avg_time;
                                    
                                    const sign = changeValue >= 0 ? '+' : '';
                                    const color = changeValue >= 0 ? 'green' : 'red';
                                    return `Cambio: ${sign}${changeValue}%`;
                                }
                                return '';
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Comparación de Períodos'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    async loadComparisonChart() {
        try {
            const data = await this.fetchData(this.comparisonUrl);
            this.comparisonData = data;
            
            if (this.charts.comparison && data.current && data.previous) {
                this.charts.comparison.data.datasets[0].data = [
                    data.current.completed,
                    data.current.revenue,
                    data.current.avg_time
                ];
                this.charts.comparison.data.datasets[1].data = [
                    data.previous.completed,
                    data.previous.revenue,
                    data.previous.avg_time
                ];
                this.charts.comparison.update();
            }
        } catch (error) {
            console.error('Error loading comparison chart:', error);
        }
    }
    
    // ========== Métodos auxiliares ==========
    async fetchData(url) {
        const params = new URLSearchParams({
            period: this.period
        });
        if (this.dateFrom) params.append('start_date', this.dateFrom);
        if (this.dateTo) params.append('end_date', this.dateTo);
        
        const fullUrl = url.includes('?') 
            ? `${url}&${params.toString()}`
            : `${url}?${params.toString()}`;
        
        const response = await fetch(fullUrl, {
            headers: {
                'X-CSRFToken': this.csrfToken
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    updatePeriod(period, dateFrom, dateTo) {
        this.period = period;
        this.dateFrom = dateFrom;
        this.dateTo = dateTo;
        this.loadAllCharts();
    }
    
    exportChart(chartId, format = 'png') {
        const chart = this.charts[chartId];
        if (!chart) {
            console.error(`Chart ${chartId} not found`);
            return;
        }
        
        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = `chart-${chartId}.${format}`;
        link.href = url;
        link.click();
    }
    
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
    }
}

// Instancia global
window.ServiceDashboardCharts = {
    instance: null,
    
    init: function(options) {
        if (this.instance) {
            this.instance.destroy();
        }
        this.instance = new ServiceDashboardCharts(options);
        return this.instance;
    },
    
    updatePeriod: function(period, dateFrom, dateTo) {
        if (this.instance) {
            this.instance.updatePeriod(period, dateFrom, dateTo);
        }
    },
    
    exportChart: function(chartId, format) {
        if (this.instance) {
            this.instance.exportChart(chartId, format);
        }
    }
};
