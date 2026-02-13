// ForgeDB Frontend - Main JavaScript

// Global configuration
const ForgeDB = {
    config: {
        apiBaseUrl: '/api/v1/',
        refreshInterval: 30000, // 30 seconds
        chartColors: {
            primary: '#0d6efd',
            secondary: '#6c757d',
            success: '#198754',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#0dcaf0'
        }
    },
    
    // Utility functions
    utils: {
        // Format currency
        formatCurrency: function(amount) {
            return new Intl.NumberFormat('es-MX', {
                style: 'currency',
                currency: 'MXN'
            }).format(amount);
        },
        
        // Format date
        formatDate: function(dateString) {
            return new Intl.DateTimeFormat('es-MX', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            }).format(new Date(dateString));
        },
        
        // Format datetime
        formatDateTime: function(dateString) {
            return new Intl.DateTimeFormat('es-MX', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(new Date(dateString));
        },
        
        // Show loading spinner
        showLoading: function(element) {
            const spinner = document.createElement('div');
            spinner.className = 'loading-spinner me-2';
            spinner.id = 'loading-spinner';
            element.prepend(spinner);
        },
        
        // Hide loading spinner
        hideLoading: function() {
            const spinner = document.getElementById('loading-spinner');
            if (spinner) {
                spinner.remove();
            }
        },
        
        // Show toast notification
        showToast: function(message, type = 'info') {
            if (typeof bootstrap === 'undefined') {
                console.error('Bootstrap is not loaded');
                alert(message); // Fallback to alert if Bootstrap is not available
                return;
            }
            
            const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
            const toast = this.createToast(message, type);
            toastContainer.appendChild(toast);
            
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
            
            // Remove toast after it's hidden
            toast.addEventListener('hidden.bs.toast', function() {
                toast.remove();
            });
        },
        
        // Create toast container
        createToastContainer: function() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
            return container;
        },
        
        // Create toast element
        createToast: function(message, type) {
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.setAttribute('role', 'alert');
            
            const iconMap = {
                success: 'check-circle-fill',
                danger: 'exclamation-triangle-fill',
                warning: 'exclamation-triangle-fill',
                info: 'info-circle-fill'
            };
            
            toast.innerHTML = `
                <div class="toast-header">
                    <i class="bi bi-${iconMap[type]} text-${type} me-2"></i>
                    <strong class="me-auto">ForgeDB</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            `;
            
            return toast;
        }
    },
    
    // API helper functions
    api: {
        // Get CSRF token
        getCSRFToken: function() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        },
        
        // Make API request
        request: async function(url, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            };
            
            const config = { ...defaultOptions, ...options };
            config.headers = { ...defaultOptions.headers, ...options.headers };
            
            try {
                const response = await fetch(ForgeDB.config.apiBaseUrl + url, config);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('API request failed:', error);
                ForgeDB.utils.showToast('Error en la comunicación con el servidor', 'danger');
                throw error;
            }
        },
        
        // GET request
        get: function(url) {
            return this.request(url, { method: 'GET' });
        },
        
        // POST request
        post: function(url, data) {
            return this.request(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },
        
        // PUT request
        put: function(url, data) {
            return this.request(url, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },
        
        // DELETE request
        delete: function(url) {
            return this.request(url, { method: 'DELETE' });
        }
    },
    
    // Chart utilities
    charts: {
        // Default chart options
        defaultOptions: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        },
        
        // Create line chart
        createLineChart: function(ctx, data, options = {}) {
            return new Chart(ctx, {
                type: 'line',
                data: data,
                options: { ...this.defaultOptions, ...options }
            });
        },
        
        // Create bar chart
        createBarChart: function(ctx, data, options = {}) {
            return new Chart(ctx, {
                type: 'bar',
                data: data,
                options: { ...this.defaultOptions, ...options }
            });
        },
        
        // Create doughnut chart
        createDoughnutChart: function(ctx, data, options = {}) {
            return new Chart(ctx, {
                type: 'doughnut',
                data: data,
                options: { ...this.defaultOptions, ...options }
            });
        }
    },
    
    // Form utilities
    forms: {
        // Serialize form data
        serialize: function(form) {
            const formData = new FormData(form);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                if (data[key]) {
                    if (Array.isArray(data[key])) {
                        data[key].push(value);
                    } else {
                        data[key] = [data[key], value];
                    }
                } else {
                    data[key] = value;
                }
            }
            
            return data;
        },
        
        // Validate form
        validate: function(form) {
            const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('is-invalid');
                    isValid = false;
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            return isValid;
        },
        
        // Clear form validation
        clearValidation: function(form) {
            const inputs = form.querySelectorAll('.is-invalid, .is-valid');
            inputs.forEach(input => {
                input.classList.remove('is-invalid', 'is-valid');
            });
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Register service worker for PWA functionality
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/frontend/js/sw.js')
            .then(function(registration) {
                console.log('Service Worker registered successfully:', registration.scope);
                
                // Check for updates
                registration.addEventListener('updatefound', function() {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', function() {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New content is available, show update notification
                            ForgeDB.utils.showToast('Nueva versión disponible. Recarga la página para actualizar.', 'info');
                        }
                    });
                });
            })
            .catch(function(error) {
                console.error('Service Worker registration failed:', error);
            });
    }
    
    // Wait for Bootstrap to be available
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded');
        return;
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
    
    // Add fade-in animation to main content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
    
    // Initialize search functionality
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        let timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                // Trigger search after 300ms delay
                const event = new CustomEvent('search', { detail: { query: this.value } });
                this.dispatchEvent(event);
            }, 300);
        });
    });
    
    console.log('ForgeDB Frontend initialized successfully');
});

// Export for global use
window.ForgeDB = ForgeDB;

// Alias MovIAx para compatibilidad con nuevo branding
window.MovIAx = ForgeDB;