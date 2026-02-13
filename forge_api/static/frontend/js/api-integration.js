/**
 * API Integration with Error Handling and User Feedback
 * ForgeDB Frontend Application
 */

// ===== ENHANCED API CLIENT =====

class EnhancedAPIClient {
    constructor() {
        this.baseURL = '/api/v1/';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };
        this.requestInterceptors = [];
        this.responseInterceptors = [];
        
        this.setupCSRFToken();
        this.setupDefaultInterceptors();
    }
    
    setupCSRFToken() {
        // Get CSRF token from cookie or meta tag
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
            this.defaultHeaders['X-CSRFToken'] = csrfToken;
        }
    }
    
    getCSRFToken() {
        // Try to get from cookie first
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
            
        if (cookieValue) return cookieValue;
        
        // Try to get from meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : null;
    }
    
    setupDefaultInterceptors() {
        // Request interceptor for loading states
        this.addRequestInterceptor((config) => {
            if (config.showLoading !== false) {
                const target = config.loadingTarget || 'global';
                const message = config.loadingMessage || 'Cargando...';
                config._loaderId = window.userFeedback?.loading.showLoading(target, message);
            }
            return config;
        });
        
        // Response interceptor for error handling and loading cleanup
        this.addResponseInterceptor(
            (response) => {
                // Hide loading state
                if (response.config._loaderId) {
                    window.userFeedback?.loading.hideLoading(response.config._loaderId);
                }
                return response;
            },
            (error) => {
                // Hide loading state
                if (error.config?._loaderId) {
                    window.userFeedback?.loading.hideLoading(error.config._loaderId);
                }
                
                // Handle error with error handler
                if (window.errorHandler) {
                    window.errorHandler.handleApiError(error.response || {
                        status: 0,
                        url: error.config?.url || 'unknown'
                    }, {
                        method: error.config?.method || 'GET',
                        retryCallback: () => this.retry(error.config)
                    });
                }
                
                throw error;
            }
        );
    }
    
    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }
    
    addResponseInterceptor(onSuccess, onError) {
        this.responseInterceptors.push({ onSuccess, onError });
    }
    
    async request(config) {
        // Apply request interceptors
        let processedConfig = { ...config };
        for (const interceptor of this.requestInterceptors) {
            processedConfig = await interceptor(processedConfig);
        }
        
        // Prepare request
        const url = processedConfig.url.startsWith('http') ? 
            processedConfig.url : 
            `${this.baseURL}${processedConfig.url.replace(/^\//, '')}`;
            
        const options = {
            method: processedConfig.method || 'GET',
            headers: {
                ...this.defaultHeaders,
                ...processedConfig.headers
            }
        };
        
        if (processedConfig.data) {
            options.body = JSON.stringify(processedConfig.data);
        }
        
        if (processedConfig.params) {
            const searchParams = new URLSearchParams(processedConfig.params);
            const separator = url.includes('?') ? '&' : '?';
            url += separator + searchParams.toString();
        }
        
        try {
            const response = await fetch(url, options);
            
            // Create response object similar to axios
            const responseObj = {
                data: null,
                status: response.status,
                statusText: response.statusText,
                headers: response.headers,
                config: processedConfig,
                request: response
            };
            
            // Parse response data
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                responseObj.data = await response.json();
            } else {
                responseObj.data = await response.text();
            }
            
            // Check if response is successful
            if (!response.ok) {
                const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
                error.response = responseObj;
                error.config = processedConfig;
                throw error;
            }
            
            // Apply response interceptors (success)
            let processedResponse = responseObj;
            for (const interceptor of this.responseInterceptors) {
                if (interceptor.onSuccess) {
                    processedResponse = await interceptor.onSuccess(processedResponse);
                }
            }
            
            return processedResponse;
            
        } catch (error) {
            // Apply response interceptors (error)
            for (const interceptor of this.responseInterceptors) {
                if (interceptor.onError) {
                    try {
                        await interceptor.onError(error);
                    } catch (interceptorError) {
                        // If interceptor throws, use that error instead
                        throw interceptorError;
                    }
                }
            }
            
            throw error;
        }
    }
    
    async retry(config) {
        return this.request(config);
    }
    
    // Convenience methods
    get(url, config = {}) {
        return this.request({ ...config, method: 'GET', url });
    }
    
    post(url, data, config = {}) {
        return this.request({ ...config, method: 'POST', url, data });
    }
    
    put(url, data, config = {}) {
        return this.request({ ...config, method: 'PUT', url, data });
    }
    
    patch(url, data, config = {}) {
        return this.request({ ...config, method: 'PATCH', url, data });
    }
    
    delete(url, config = {}) {
        return this.request({ ...config, method: 'DELETE', url });
    }
}

// ===== FORM INTEGRATION =====

class FormHandler {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.setupFormHandlers();
    }
    
    setupFormHandlers() {
        document.addEventListener('submit', (event) => {
            if (event.target.hasAttribute('data-api-form')) {
                event.preventDefault();
                this.handleFormSubmit(event.target);
            }
        });
    }
    
    async handleFormSubmit(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Get form configuration
        const method = form.getAttribute('data-method') || 'POST';
        const url = form.getAttribute('action') || form.getAttribute('data-url');
        const successMessage = form.getAttribute('data-success-message') || 'Operación completada exitosamente';
        const redirectUrl = form.getAttribute('data-redirect');
        
        if (!url) {
            window.errorHandler?.showError('URL de formulario no especificada');
            return;
        }
        
        try {
            // Clear previous form errors
            this.clearFormErrors(form);
            
            // Submit form
            const response = await this.apiClient.request({
                method: method,
                url: url,
                data: data,
                loadingTarget: form.querySelector('button[type="submit"]'),
                loadingMessage: 'Enviando...'
            });
            
            // Show success message
            window.userFeedback?.toast.success(successMessage);
            
            // Handle redirect or reset form
            if (redirectUrl) {
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1000);
            } else {
                form.reset();
            }
            
            // Trigger custom success event
            form.dispatchEvent(new CustomEvent('formSuccess', {
                detail: { response: response.data }
            }));
            
        } catch (error) {
            // Handle validation errors
            if (error.response?.status === 422 || error.response?.status === 400) {
                this.displayFormErrors(form, error.response.data);
            }
            
            // Trigger custom error event
            form.dispatchEvent(new CustomEvent('formError', {
                detail: { error: error }
            }));
        }
    }
    
    displayFormErrors(form, errors) {
        if (window.errorHandler) {
            window.errorHandler.handleFormValidationErrors(form, errors);
        }
    }
    
    clearFormErrors(form) {
        if (window.errorHandler) {
            window.errorHandler.clearFormErrors(form);
        }
    }
}

// ===== DATA LOADING UTILITIES =====

class DataLoader {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.setupDataLoaders();
    }
    
    setupDataLoaders() {
        // Auto-load data for elements with data-load attribute
        document.addEventListener('DOMContentLoaded', () => {
            this.loadAllDataElements();
        });
        
        // Setup refresh buttons
        document.addEventListener('click', (event) => {
            if (event.target.hasAttribute('data-refresh')) {
                event.preventDefault();
                const target = event.target.getAttribute('data-refresh');
                this.refreshData(target);
            }
        });
    }
    
    loadAllDataElements() {
        document.querySelectorAll('[data-load]').forEach(element => {
            this.loadElementData(element);
        });
    }
    
    async loadElementData(element) {
        const url = element.getAttribute('data-load');
        const template = element.getAttribute('data-template');
        const emptyMessage = element.getAttribute('data-empty-message') || 'No hay datos disponibles';
        
        if (!url) return;
        
        try {
            const response = await this.apiClient.get(url, {
                loadingTarget: element,
                loadingMessage: 'Cargando datos...'
            });
            
            const data = response.data;
            
            // Check if data is empty
            if (!data || (Array.isArray(data) && data.length === 0) || 
                (data.results && Array.isArray(data.results) && data.results.length === 0)) {
                
                window.userFeedback?.emptyState.show(element, {
                    title: 'Sin datos',
                    message: emptyMessage
                });
                return;
            }
            
            // Render data
            if (template) {
                this.renderTemplate(element, data, template);
            } else {
                this.renderDefaultData(element, data);
            }
            
            // Trigger data loaded event
            element.dispatchEvent(new CustomEvent('dataLoaded', {
                detail: { data: data }
            }));
            
        } catch (error) {
            window.userFeedback?.emptyState.showError(element, 
                'Error al cargar los datos. Intente nuevamente.');
        }
    }
    
    renderTemplate(element, data, templateId) {
        const template = document.getElementById(templateId);
        if (!template) {
            console.error(`Template ${templateId} not found`);
            return;
        }
        
        // Simple template rendering (you might want to use a proper template engine)
        let html = template.innerHTML;
        
        // Handle arrays of data
        if (Array.isArray(data) || (data.results && Array.isArray(data.results))) {
            const items = Array.isArray(data) ? data : data.results;
            const itemTemplate = html;
            html = items.map(item => this.interpolateTemplate(itemTemplate, item)).join('');
        } else {
            html = this.interpolateTemplate(html, data);
        }
        
        element.innerHTML = html;
    }
    
    interpolateTemplate(template, data) {
        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return data[key] || '';
        });
    }
    
    renderDefaultData(element, data) {
        // Simple default rendering for debugging
        element.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }
    
    refreshData(selector) {
        const elements = selector ? document.querySelectorAll(selector) : 
                        document.querySelectorAll('[data-load]');
        
        elements.forEach(element => {
            this.loadElementData(element);
        });
    }
}

// ===== SEARCH INTEGRATION =====

class SearchHandler {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.setupSearchHandlers();
    }
    
    setupSearchHandlers() {
        document.addEventListener('input', (event) => {
            if (event.target.hasAttribute('data-search')) {
                this.handleSearchInput(event.target);
            }
        });
    }
    
    handleSearchInput(input) {
        const url = input.getAttribute('data-search');
        const resultsContainer = input.getAttribute('data-results');
        const minLength = parseInt(input.getAttribute('data-min-length') || '2');
        
        if (!url || !resultsContainer) return;
        
        const query = input.value.trim();
        
        if (query.length < minLength) {
            this.clearSearchResults(resultsContainer);
            return;
        }
        
        // Debounce search
        clearTimeout(input._searchTimeout);
        input._searchTimeout = setTimeout(() => {
            this.performSearch(url, query, resultsContainer);
        }, 300);
    }
    
    async performSearch(url, query, resultsContainer) {
        const container = document.querySelector(resultsContainer);
        if (!container) return;
        
        try {
            const response = await this.apiClient.get(url, {
                params: { search: query },
                loadingTarget: container,
                loadingMessage: 'Buscando...'
            });
            
            const results = response.data.results || response.data;
            
            if (results.length === 0) {
                window.userFeedback?.emptyState.showNoResults(container, query);
            } else {
                this.renderSearchResults(container, results);
            }
            
        } catch (error) {
            window.userFeedback?.emptyState.showError(container, 
                'Error en la búsqueda. Intente nuevamente.');
        }
    }
    
    renderSearchResults(container, results) {
        // Simple results rendering
        const html = results.map(result => `
            <div class="search-result p-2 border-bottom">
                <div class="fw-bold">${result.name || result.title || result.id}</div>
                ${result.description ? `<div class="text-muted small">${result.description}</div>` : ''}
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    clearSearchResults(resultsContainer) {
        const container = document.querySelector(resultsContainer);
        if (container) {
            container.innerHTML = '';
        }
    }
}

// ===== INITIALIZATION =====

// Initialize API integration when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Create enhanced API client
    window.apiClient = new EnhancedAPIClient();
    
    // Initialize form handler
    window.formHandler = new FormHandler(window.apiClient);
    
    // Initialize data loader
    window.dataLoader = new DataLoader(window.apiClient);
    
    // Initialize search handler
    window.searchHandler = new SearchHandler(window.apiClient);
    
    console.log('API integration initialized');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        EnhancedAPIClient,
        FormHandler,
        DataLoader,
        SearchHandler
    };
}