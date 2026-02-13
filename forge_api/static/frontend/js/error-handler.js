/**
 * Comprehensive Error Handling System
 * ForgeDB Frontend Application
 */

// ===== ERROR TYPES AND CONSTANTS =====

const ERROR_TYPES = {
    API_ERROR: 'api_error',
    VALIDATION_ERROR: 'validation_error',
    NETWORK_ERROR: 'network_error',
    AUTHENTICATION_ERROR: 'auth_error',
    PERMISSION_ERROR: 'permission_error',
    CLIENT_ERROR: 'client_error',
    SERVER_ERROR: 'server_error',
    TIMEOUT_ERROR: 'timeout_error',
    UNKNOWN_ERROR: 'unknown_error'
};

const ERROR_SEVERITY = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    CRITICAL: 'critical'
};

const RETRY_STRATEGIES = {
    NONE: 'none',
    IMMEDIATE: 'immediate',
    EXPONENTIAL_BACKOFF: 'exponential_backoff',
    LINEAR_BACKOFF: 'linear_backoff'
};

// ===== MAIN ERROR HANDLER CLASS =====

class ErrorHandler {
    constructor() {
        this.errorQueue = [];
        this.retryAttempts = new Map();
        this.maxRetries = 3;
        this.baseRetryDelay = 1000; // 1 second
        this.errorCallbacks = new Map();
        this.globalErrorHandler = null;
        
        this.init();
    }
    
    init() {
        // Set up global error handlers
        this.setupGlobalErrorHandlers();
        
        // Initialize error display container
        this.initializeErrorContainer();
        
        // Set up periodic error queue processing
        this.startErrorQueueProcessor();
    }
    
    setupGlobalErrorHandlers() {
        // Handle uncaught JavaScript errors
        window.addEventListener('error', (event) => {
            this.handleError({
                type: ERROR_TYPES.CLIENT_ERROR,
                message: event.message,
                source: event.filename,
                line: event.lineno,
                column: event.colno,
                error: event.error,
                severity: ERROR_SEVERITY.HIGH
            });
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError({
                type: ERROR_TYPES.CLIENT_ERROR,
                message: 'Unhandled Promise Rejection',
                error: event.reason,
                severity: ERROR_SEVERITY.MEDIUM
            });
        });
        
        // Handle network errors
        window.addEventListener('offline', () => {
            this.handleError({
                type: ERROR_TYPES.NETWORK_ERROR,
                message: 'Conexión perdida. Trabajando en modo offline.',
                severity: ERROR_SEVERITY.MEDIUM,
                recoverable: true
            });
        });
        
        window.addEventListener('online', () => {
            this.showSuccess('Conexión restaurada. Sincronizando datos...');
            this.retryFailedRequests();
        });
    }
    
    initializeErrorContainer() {
        if (!document.getElementById('error-container')) {
            const container = document.createElement('div');
            container.id = 'error-container';
            container.className = 'error-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
    }
    
    startErrorQueueProcessor() {
        setInterval(() => {
            this.processErrorQueue();
        }, 5000); // Process every 5 seconds
    }
    
    // ===== ERROR HANDLING METHODS =====
    
    handleError(errorInfo) {
        const error = this.normalizeError(errorInfo);
        
        // Log error for debugging
        console.error('Error handled:', error);
        
        // Add to error queue for processing
        this.errorQueue.push(error);
        
        // Immediate handling for critical errors
        if (error.severity === ERROR_SEVERITY.CRITICAL) {
            this.displayError(error);
        }
        
        // Call registered callbacks
        this.notifyErrorCallbacks(error);
        
        // Attempt recovery if possible
        if (error.recoverable) {
            this.attemptRecovery(error);
        }
        
        return error;
    }
    
    normalizeError(errorInfo) {
        const error = {
            id: this.generateErrorId(),
            timestamp: new Date().toISOString(),
            type: errorInfo.type || ERROR_TYPES.UNKNOWN_ERROR,
            message: errorInfo.message || 'Ha ocurrido un error inesperado',
            details: errorInfo.details || null,
            severity: errorInfo.severity || ERROR_SEVERITY.MEDIUM,
            recoverable: errorInfo.recoverable || false,
            retryStrategy: errorInfo.retryStrategy || RETRY_STRATEGIES.NONE,
            context: errorInfo.context || {},
            source: errorInfo.source || 'unknown',
            stack: errorInfo.error?.stack || null
        };
        
        return error;
    }
    
    generateErrorId() {
        return 'err_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // ===== API ERROR HANDLING =====
    
    handleApiError(response, context = {}) {
        let errorType = ERROR_TYPES.API_ERROR;
        let severity = ERROR_SEVERITY.MEDIUM;
        let message = 'Error en la comunicación con el servidor';
        let recoverable = false;
        let retryStrategy = RETRY_STRATEGIES.NONE;
        
        // Determine error type based on status code
        if (response.status >= 400 && response.status < 500) {
            // Client errors
            switch (response.status) {
                case 400:
                    message = 'Solicitud inválida. Verifique los datos enviados.';
                    break;
                case 401:
                    errorType = ERROR_TYPES.AUTHENTICATION_ERROR;
                    message = 'Sesión expirada. Por favor, inicie sesión nuevamente.';
                    recoverable = true;
                    break;
                case 403:
                    errorType = ERROR_TYPES.PERMISSION_ERROR;
                    message = 'No tiene permisos para realizar esta acción.';
                    break;
                case 404:
                    message = 'El recurso solicitado no fue encontrado.';
                    break;
                case 422:
                    errorType = ERROR_TYPES.VALIDATION_ERROR;
                    message = 'Los datos enviados contienen errores de validación.';
                    break;
                case 429:
                    message = 'Demasiadas solicitudes. Intente nuevamente en unos momentos.';
                    recoverable = true;
                    retryStrategy = RETRY_STRATEGIES.EXPONENTIAL_BACKOFF;
                    break;
                default:
                    message = `Error del cliente (${response.status})`;
            }
        } else if (response.status >= 500) {
            // Server errors
            errorType = ERROR_TYPES.SERVER_ERROR;
            severity = ERROR_SEVERITY.HIGH;
            recoverable = true;
            retryStrategy = RETRY_STRATEGIES.EXPONENTIAL_BACKOFF;
            
            switch (response.status) {
                case 500:
                    message = 'Error interno del servidor. Intente nuevamente.';
                    break;
                case 502:
                    message = 'Servidor no disponible temporalmente.';
                    break;
                case 503:
                    message = 'Servicio temporalmente no disponible.';
                    break;
                case 504:
                    errorType = ERROR_TYPES.TIMEOUT_ERROR;
                    message = 'Tiempo de espera agotado. Intente nuevamente.';
                    break;
                default:
                    message = `Error del servidor (${response.status})`;
            }
        }
        
        return this.handleError({
            type: errorType,
            message: message,
            severity: severity,
            recoverable: recoverable,
            retryStrategy: retryStrategy,
            context: {
                ...context,
                status: response.status,
                url: response.url,
                method: context.method || 'GET'
            }
        });
    }
    
    // ===== FORM VALIDATION ERROR HANDLING =====
    
    handleFormValidationErrors(form, errors) {
        // Clear previous errors
        this.clearFormErrors(form);
        
        const errorMessages = [];
        
        // Handle field-specific errors
        Object.keys(errors).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            const fieldErrors = Array.isArray(errors[fieldName]) ? errors[fieldName] : [errors[fieldName]];
            
            if (field) {
                this.displayFieldError(field, fieldErrors);
            }
            
            errorMessages.push(...fieldErrors);
        });
        
        // Display general form error
        if (errorMessages.length > 0) {
            this.handleError({
                type: ERROR_TYPES.VALIDATION_ERROR,
                message: 'Por favor, corrija los errores en el formulario.',
                details: errorMessages,
                severity: ERROR_SEVERITY.LOW,
                context: { form: form.id || 'unknown' }
            });
        }
    }
    
    displayFieldError(field, errors) {
        // Add error class to field
        field.classList.add('is-invalid');
        
        // Remove existing error messages
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
        
        // Create error message element
        const errorElement = document.createElement('div');
        errorElement.className = 'invalid-feedback';
        errorElement.innerHTML = errors.join('<br>');
        
        // Insert error message after field
        field.parentNode.appendChild(errorElement);
        
        // Remove error on field change
        const removeError = () => {
            field.classList.remove('is-invalid');
            const errorMsg = field.parentNode.querySelector('.invalid-feedback');
            if (errorMsg) {
                errorMsg.remove();
            }
            field.removeEventListener('input', removeError);
            field.removeEventListener('change', removeError);
        };
        
        field.addEventListener('input', removeError);
        field.addEventListener('change', removeError);
    }
    
    clearFormErrors(form) {
        // Remove error classes and messages
        form.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        
        form.querySelectorAll('.invalid-feedback').forEach(error => {
            error.remove();
        });
    }
    
    // ===== ERROR DISPLAY METHODS =====
    
    displayError(error) {
        const container = document.getElementById('error-container');
        if (!container) return;
        
        const errorElement = this.createErrorElement(error);
        container.appendChild(errorElement);
        
        // Auto-remove after delay based on severity
        const delay = this.getAutoRemoveDelay(error.severity);
        if (delay > 0) {
            setTimeout(() => {
                this.removeErrorElement(errorElement);
            }, delay);
        }
    }
    
    createErrorElement(error) {
        const element = document.createElement('div');
        element.className = `alert alert-${this.getBootstrapAlertClass(error.type)} alert-dismissible fade show`;
        element.setAttribute('data-error-id', error.id);
        
        const icon = this.getErrorIcon(error.type);
        const actions = this.createErrorActions(error);
        
        element.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="bi ${icon} me-2 flex-shrink-0"></i>
                <div class="flex-grow-1">
                    <strong>${this.getErrorTitle(error.type)}</strong>
                    <div class="mt-1">${error.message}</div>
                    ${error.details ? `<small class="text-muted">${error.details}</small>` : ''}
                    ${actions}
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        return element;
    }
    
    createErrorActions(error) {
        let actions = '';
        
        if (error.recoverable) {
            actions += `
                <div class="mt-2">
                    <button class="btn btn-sm btn-outline-primary me-2" onclick="errorHandler.retryError('${error.id}')">
                        <i class="bi bi-arrow-clockwise me-1"></i>Reintentar
                    </button>
                </div>
            `;
        }
        
        if (error.type === ERROR_TYPES.AUTHENTICATION_ERROR) {
            actions += `
                <div class="mt-2">
                    <button class="btn btn-sm btn-primary" onclick="window.location.href='/frontend/login/'">
                        <i class="bi bi-box-arrow-in-right me-1"></i>Iniciar Sesión
                    </button>
                </div>
            `;
        }
        
        return actions;
    }
    
    getBootstrapAlertClass(errorType) {
        switch (errorType) {
            case ERROR_TYPES.VALIDATION_ERROR:
                return 'warning';
            case ERROR_TYPES.AUTHENTICATION_ERROR:
            case ERROR_TYPES.PERMISSION_ERROR:
                return 'info';
            case ERROR_TYPES.NETWORK_ERROR:
                return 'secondary';
            default:
                return 'danger';
        }
    }
    
    getErrorIcon(errorType) {
        switch (errorType) {
            case ERROR_TYPES.VALIDATION_ERROR:
                return 'bi-exclamation-triangle';
            case ERROR_TYPES.AUTHENTICATION_ERROR:
                return 'bi-shield-exclamation';
            case ERROR_TYPES.PERMISSION_ERROR:
                return 'bi-lock';
            case ERROR_TYPES.NETWORK_ERROR:
                return 'bi-wifi-off';
            case ERROR_TYPES.SERVER_ERROR:
                return 'bi-server';
            default:
                return 'bi-exclamation-circle';
        }
    }
    
    getErrorTitle(errorType) {
        switch (errorType) {
            case ERROR_TYPES.VALIDATION_ERROR:
                return 'Error de Validación';
            case ERROR_TYPES.AUTHENTICATION_ERROR:
                return 'Error de Autenticación';
            case ERROR_TYPES.PERMISSION_ERROR:
                return 'Sin Permisos';
            case ERROR_TYPES.NETWORK_ERROR:
                return 'Error de Conexión';
            case ERROR_TYPES.SERVER_ERROR:
                return 'Error del Servidor';
            case ERROR_TYPES.API_ERROR:
                return 'Error de API';
            default:
                return 'Error';
        }
    }
    
    getAutoRemoveDelay(severity) {
        switch (severity) {
            case ERROR_SEVERITY.LOW:
                return 5000; // 5 seconds
            case ERROR_SEVERITY.MEDIUM:
                return 8000; // 8 seconds
            case ERROR_SEVERITY.HIGH:
                return 12000; // 12 seconds
            case ERROR_SEVERITY.CRITICAL:
                return 0; // Manual dismiss only
            default:
                return 6000; // 6 seconds
        }
    }
    
    removeErrorElement(element) {
        if (element && element.parentNode) {
            element.classList.remove('show');
            setTimeout(() => {
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
            }, 150); // Bootstrap fade transition time
        }
    }
    
    // ===== RECOVERY MECHANISMS =====
    
    attemptRecovery(error) {
        switch (error.type) {
            case ERROR_TYPES.AUTHENTICATION_ERROR:
                this.handleAuthenticationRecovery();
                break;
            case ERROR_TYPES.NETWORK_ERROR:
                this.handleNetworkRecovery();
                break;
            case ERROR_TYPES.SERVER_ERROR:
            case ERROR_TYPES.TIMEOUT_ERROR:
                this.scheduleRetry(error);
                break;
        }
    }
    
    handleAuthenticationRecovery() {
        // Try to refresh token if available
        if (window.apiClient && typeof window.apiClient.refreshToken === 'function') {
            window.apiClient.refreshToken()
                .then(() => {
                    this.showSuccess('Sesión renovada exitosamente.');
                })
                .catch(() => {
                    // Redirect to login if refresh fails
                    setTimeout(() => {
                        window.location.href = '/frontend/login/';
                    }, 2000);
                });
        }
    }
    
    handleNetworkRecovery() {
        // Queue failed requests for retry when online
        this.queueOfflineRequests();
    }
    
    scheduleRetry(error) {
        const retryKey = error.context.url || error.id;
        const currentAttempts = this.retryAttempts.get(retryKey) || 0;
        
        if (currentAttempts < this.maxRetries) {
            const delay = this.calculateRetryDelay(error.retryStrategy, currentAttempts);
            
            setTimeout(() => {
                this.retryError(error.id);
            }, delay);
            
            this.retryAttempts.set(retryKey, currentAttempts + 1);
        }
    }
    
    calculateRetryDelay(strategy, attempt) {
        switch (strategy) {
            case RETRY_STRATEGIES.IMMEDIATE:
                return 0;
            case RETRY_STRATEGIES.LINEAR_BACKOFF:
                return this.baseRetryDelay * (attempt + 1);
            case RETRY_STRATEGIES.EXPONENTIAL_BACKOFF:
                return this.baseRetryDelay * Math.pow(2, attempt);
            default:
                return this.baseRetryDelay;
        }
    }
    
    retryError(errorId) {
        const error = this.errorQueue.find(e => e.id === errorId);
        if (!error) return;
        
        // Remove error display
        const errorElement = document.querySelector(`[data-error-id="${errorId}"]`);
        if (errorElement) {
            this.removeErrorElement(errorElement);
        }
        
        // Trigger retry callback if available
        if (error.context.retryCallback) {
            error.context.retryCallback();
        }
    }
    
    // ===== SUCCESS MESSAGES =====
    
    showSuccess(message, duration = 4000) {
        const container = document.getElementById('error-container');
        if (!container) return;
        
        const element = document.createElement('div');
        element.className = 'alert alert-success alert-dismissible fade show';
        element.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-check-circle me-2"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        container.appendChild(element);
        
        if (duration > 0) {
            setTimeout(() => {
                this.removeErrorElement(element);
            }, duration);
        }
    }
    
    // ===== UTILITY METHODS =====
    
    processErrorQueue() {
        // Process queued errors that haven't been displayed
        const unprocessedErrors = this.errorQueue.filter(error => 
            error.severity !== ERROR_SEVERITY.CRITICAL && 
            !document.querySelector(`[data-error-id="${error.id}"]`)
        );
        
        unprocessedErrors.slice(0, 3).forEach(error => {
            this.displayError(error);
        });
    }
    
    clearAllErrors() {
        const container = document.getElementById('error-container');
        if (container) {
            container.innerHTML = '';
        }
        this.errorQueue = [];
    }
    
    registerErrorCallback(type, callback) {
        if (!this.errorCallbacks.has(type)) {
            this.errorCallbacks.set(type, []);
        }
        this.errorCallbacks.get(type).push(callback);
    }
    
    notifyErrorCallbacks(error) {
        const callbacks = this.errorCallbacks.get(error.type) || [];
        callbacks.forEach(callback => {
            try {
                callback(error);
            } catch (e) {
                console.error('Error in error callback:', e);
            }
        });
    }
    
    // ===== PUBLIC API METHODS =====
    
    // Method to be called by other modules
    static handleApiResponse(response, context = {}) {
        if (!window.errorHandler) {
            window.errorHandler = new ErrorHandler();
        }
        
        if (!response.ok) {
            return window.errorHandler.handleApiError(response, context);
        }
        
        return null;
    }
    
    static handleFormErrors(form, errors) {
        if (!window.errorHandler) {
            window.errorHandler = new ErrorHandler();
        }
        
        return window.errorHandler.handleFormValidationErrors(form, errors);
    }
    
    static showError(message, type = ERROR_TYPES.CLIENT_ERROR, severity = ERROR_SEVERITY.MEDIUM) {
        if (!window.errorHandler) {
            window.errorHandler = new ErrorHandler();
        }
        
        return window.errorHandler.handleError({
            type: type,
            message: message,
            severity: severity
        });
    }
    
    static showSuccess(message, duration = 4000) {
        if (!window.errorHandler) {
            window.errorHandler = new ErrorHandler();
        }
        
        return window.errorHandler.showSuccess(message, duration);
    }
}

// ===== INITIALIZATION =====

// Initialize error handler when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (!window.errorHandler) {
        window.errorHandler = new ErrorHandler();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ErrorHandler,
        ERROR_TYPES,
        ERROR_SEVERITY,
        RETRY_STRATEGIES
    };
}