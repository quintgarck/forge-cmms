/**
 * User Feedback and Loading States System
 * ForgeDB Frontend Application
 */

// ===== LOADING STATES MANAGER =====

class LoadingStateManager {
    constructor() {
        this.activeLoaders = new Map();
        this.globalLoadingCount = 0;
        this.init();
    }
    
    init() {
        this.createGlobalLoader();
        this.setupFormLoadingStates();
    }
    
    createGlobalLoader() {
        if (!document.getElementById('global-loader')) {
            const loader = document.createElement('div');
            loader.id = 'global-loader';
            loader.className = 'global-loader position-fixed top-0 start-0 w-100 h-100 d-none';
            loader.style.cssText = `
                background: rgba(255, 255, 255, 0.8);
                z-index: 9998;
                backdrop-filter: blur(2px);
            `;
            
            loader.innerHTML = `
                <div class="d-flex justify-content-center align-items-center h-100">
                    <div class="text-center">
                        <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <div class="loading-text">Cargando...</div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(loader);
        }
    }
    
    setupFormLoadingStates() {
        // Auto-setup loading states for forms
        document.addEventListener('submit', (event) => {
            if (event.target.tagName === 'FORM') {
                this.showFormLoading(event.target);
            }
        });
    }
    
    // ===== LOADING METHODS =====
    
    showLoading(target, message = 'Cargando...') {
        const loaderId = this.generateLoaderId();
        
        if (typeof target === 'string') {
            // Target is a selector
            const element = document.querySelector(target);
            if (element) {
                this.showElementLoading(element, loaderId, message);
            }
        } else if (target instanceof HTMLElement) {
            // Target is an element
            this.showElementLoading(target, loaderId, message);
        } else if (target === 'global' || !target) {
            // Global loading
            this.showGlobalLoading(loaderId, message);
        }
        
        return loaderId;
    }
    
    showElementLoading(element, loaderId, message) {
        // Store original content
        const originalContent = element.innerHTML;
        const originalDisabled = element.disabled;
        
        this.activeLoaders.set(loaderId, {
            element: element,
            originalContent: originalContent,
            originalDisabled: originalDisabled,
            type: 'element'
        });
        
        // Show loading state
        if (element.tagName === 'BUTTON') {
            element.disabled = true;
            element.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                ${message}
            `;
        } else {
            element.style.position = 'relative';
            element.style.pointerEvents = 'none';
            
            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay position-absolute top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center';
            overlay.style.cssText = `
                background: rgba(255, 255, 255, 0.8);
                z-index: 10;
                border-radius: inherit;
            `;
            
            overlay.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary mb-2" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <div class="small">${message}</div>
                </div>
            `;
            
            element.appendChild(overlay);
        }
    }
    
    showGlobalLoading(loaderId, message) {
        this.globalLoadingCount++;
        
        this.activeLoaders.set(loaderId, {
            type: 'global'
        });
        
        const loader = document.getElementById('global-loader');
        if (loader) {
            const textElement = loader.querySelector('.loading-text');
            if (textElement) {
                textElement.textContent = message;
            }
            loader.classList.remove('d-none');
        }
    }
    
    showFormLoading(form) {
        const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            const loaderId = this.showLoading(submitButton, 'Procesando...');
            
            // Auto-hide after timeout as fallback
            setTimeout(() => {
                this.hideLoading(loaderId);
            }, 30000); // 30 seconds timeout
            
            return loaderId;
        }
    }
    
    hideLoading(loaderId) {
        const loader = this.activeLoaders.get(loaderId);
        if (!loader) return;
        
        if (loader.type === 'global') {
            this.globalLoadingCount--;
            if (this.globalLoadingCount <= 0) {
                this.globalLoadingCount = 0;
                const globalLoader = document.getElementById('global-loader');
                if (globalLoader) {
                    globalLoader.classList.add('d-none');
                }
            }
        } else if (loader.type === 'element') {
            const element = loader.element;
            
            if (element.tagName === 'BUTTON') {
                element.disabled = loader.originalDisabled;
                element.innerHTML = loader.originalContent;
            } else {
                element.style.pointerEvents = '';
                const overlay = element.querySelector('.loading-overlay');
                if (overlay) {
                    overlay.remove();
                }
            }
        }
        
        this.activeLoaders.delete(loaderId);
    }
    
    hideAllLoading() {
        this.activeLoaders.forEach((loader, loaderId) => {
            this.hideLoading(loaderId);
        });
    }
    
    generateLoaderId() {
        return 'loader_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// ===== TOAST NOTIFICATION SYSTEM =====

class ToastManager {
    constructor() {
        this.toastContainer = null;
        this.toastQueue = [];
        this.maxToasts = 5;
        this.init();
    }
    
    init() {
        this.createToastContainer();
    }
    
    createToastContainer() {
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
            this.toastContainer = container;
        } else {
            this.toastContainer = document.getElementById('toast-container');
        }
    }
    
    show(message, type = 'info', options = {}) {
        const toast = this.createToast(message, type, options);
        
        // Limit number of toasts
        if (this.toastContainer.children.length >= this.maxToasts) {
            const oldestToast = this.toastContainer.firstElementChild;
            if (oldestToast) {
                this.removeToast(oldestToast);
            }
        }
        
        this.toastContainer.appendChild(toast);
        
        // Show toast with animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Auto-hide toast
        const duration = options.duration || this.getDefaultDuration(type);
        if (duration > 0) {
            setTimeout(() => {
                this.removeToast(toast);
            }, duration);
        }
        
        return toast;
    }
    
    createToast(message, type, options) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${this.getBootstrapClass(type)} border-0`;
        toast.setAttribute('role', 'alert');
        
        const icon = this.getIcon(type);
        const title = options.title || this.getDefaultTitle(type);
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="bi ${icon} me-2"></i>
                    <div>
                        ${title ? `<div class="fw-bold">${title}</div>` : ''}
                        <div>${message}</div>
                    </div>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add click handler for close button
        const closeButton = toast.querySelector('.btn-close');
        closeButton.addEventListener('click', () => {
            this.removeToast(toast);
        });
        
        return toast;
    }
    
    removeToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300); // Bootstrap toast hide transition
    }
    
    getBootstrapClass(type) {
        switch (type) {
            case 'success': return 'success';
            case 'error': return 'danger';
            case 'warning': return 'warning';
            case 'info': return 'info';
            default: return 'secondary';
        }
    }
    
    getIcon(type) {
        switch (type) {
            case 'success': return 'bi-check-circle';
            case 'error': return 'bi-exclamation-circle';
            case 'warning': return 'bi-exclamation-triangle';
            case 'info': return 'bi-info-circle';
            default: return 'bi-bell';
        }
    }
    
    getDefaultTitle(type) {
        switch (type) {
            case 'success': return 'Éxito';
            case 'error': return 'Error';
            case 'warning': return 'Advertencia';
            case 'info': return 'Información';
            default: return null;
        }
    }
    
    getDefaultDuration(type) {
        switch (type) {
            case 'success': return 4000;
            case 'error': return 8000;
            case 'warning': return 6000;
            case 'info': return 5000;
            default: return 4000;
        }
    }
    
    // Convenience methods
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }
    
    error(message, options = {}) {
        return this.show(message, 'error', options);
    }
    
    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }
    
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
}

// ===== EMPTY STATE MANAGER =====

class EmptyStateManager {
    constructor() {
        this.emptyStates = new Map();
    }
    
    show(container, config = {}) {
        const element = typeof container === 'string' ? document.querySelector(container) : container;
        if (!element) return;
        
        const emptyState = this.createEmptyState(config);
        const emptyStateId = this.generateEmptyStateId();
        
        // Store original content
        this.emptyStates.set(emptyStateId, {
            element: element,
            originalContent: element.innerHTML
        });
        
        // Show empty state
        element.innerHTML = '';
        element.appendChild(emptyState);
        
        return emptyStateId;
    }
    
    hide(emptyStateId) {
        const state = this.emptyStates.get(emptyStateId);
        if (!state) return;
        
        // Restore original content
        state.element.innerHTML = state.originalContent;
        this.emptyStates.delete(emptyStateId);
    }
    
    createEmptyState(config) {
        const {
            icon = 'bi-inbox',
            title = 'No hay datos disponibles',
            message = 'No se encontraron elementos para mostrar.',
            actionText = null,
            actionCallback = null,
            actionUrl = null
        } = config;
        
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state text-center py-5';
        
        let actionHtml = '';
        if (actionText) {
            if (actionUrl) {
                actionHtml = `
                    <a href="${actionUrl}" class="btn btn-primary">
                        <i class="bi bi-plus-circle me-2"></i>${actionText}
                    </a>
                `;
            } else if (actionCallback) {
                const callbackId = 'callback_' + Date.now();
                window[callbackId] = actionCallback;
                actionHtml = `
                    <button class="btn btn-primary" onclick="${callbackId}()">
                        <i class="bi bi-plus-circle me-2"></i>${actionText}
                    </button>
                `;
            }
        }
        
        emptyState.innerHTML = `
            <div class="empty-state-icon mb-3">
                <i class="bi ${icon}" style="font-size: 4rem; color: #6c757d;"></i>
            </div>
            <h4 class="empty-state-title text-muted">${title}</h4>
            <p class="empty-state-message text-muted mb-4">${message}</p>
            ${actionHtml}
        `;
        
        return emptyState;
    }
    
    generateEmptyStateId() {
        return 'empty_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Predefined empty states
    showNoResults(container, searchTerm = '') {
        return this.show(container, {
            icon: 'bi-search',
            title: 'No se encontraron resultados',
            message: searchTerm ? 
                `No se encontraron resultados para "${searchTerm}". Intente con otros términos de búsqueda.` :
                'No se encontraron resultados. Intente ajustar los filtros de búsqueda.'
        });
    }
    
    showNoData(container, entityName = 'elementos') {
        return this.show(container, {
            icon: 'bi-inbox',
            title: `No hay ${entityName}`,
            message: `Aún no se han creado ${entityName}. Comience agregando el primero.`,
            actionText: `Crear ${entityName.slice(0, -1)}`,
            actionCallback: () => {
                // This should be overridden by the calling code
                console.log(`Create new ${entityName} action`);
            }
        });
    }
    
    showError(container, message = 'Ha ocurrido un error al cargar los datos.') {
        return this.show(container, {
            icon: 'bi-exclamation-triangle',
            title: 'Error al cargar',
            message: message,
            actionText: 'Reintentar',
            actionCallback: () => {
                window.location.reload();
            }
        });
    }
    
    showOffline(container) {
        return this.show(container, {
            icon: 'bi-wifi-off',
            title: 'Sin conexión',
            message: 'No se puede cargar el contenido. Verifique su conexión a internet.',
            actionText: 'Reintentar',
            actionCallback: () => {
                window.location.reload();
            }
        });
    }
}

// ===== PROGRESS INDICATOR =====

class ProgressIndicator {
    constructor() {
        this.progressBars = new Map();
    }
    
    show(container, config = {}) {
        const element = typeof container === 'string' ? document.querySelector(container) : container;
        if (!element) return;
        
        const {
            value = 0,
            max = 100,
            label = 'Progreso',
            showPercentage = true,
            animated = true,
            striped = false
        } = config;
        
        const progressId = this.generateProgressId();
        const progressBar = this.createProgressBar(value, max, label, showPercentage, animated, striped);
        
        this.progressBars.set(progressId, {
            element: element,
            progressBar: progressBar,
            originalContent: element.innerHTML
        });
        
        element.innerHTML = '';
        element.appendChild(progressBar);
        
        return progressId;
    }
    
    update(progressId, value, label = null) {
        const progress = this.progressBars.get(progressId);
        if (!progress) return;
        
        const bar = progress.progressBar.querySelector('.progress-bar');
        const labelElement = progress.progressBar.querySelector('.progress-label');
        const percentageElement = progress.progressBar.querySelector('.progress-percentage');
        
        if (bar) {
            const percentage = Math.round((value / 100) * 100);
            bar.style.width = `${percentage}%`;
            bar.setAttribute('aria-valuenow', value);
        }
        
        if (label && labelElement) {
            labelElement.textContent = label;
        }
        
        if (percentageElement) {
            percentageElement.textContent = `${Math.round(value)}%`;
        }
    }
    
    hide(progressId) {
        const progress = this.progressBars.get(progressId);
        if (!progress) return;
        
        progress.element.innerHTML = progress.originalContent;
        this.progressBars.delete(progressId);
    }
    
    createProgressBar(value, max, label, showPercentage, animated, striped) {
        const container = document.createElement('div');
        container.className = 'progress-container';
        
        const percentage = Math.round((value / max) * 100);
        
        let progressClasses = 'progress-bar';
        if (animated) progressClasses += ' progress-bar-animated';
        if (striped) progressClasses += ' progress-bar-striped';
        
        container.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="progress-label">${label}</span>
                ${showPercentage ? `<span class="progress-percentage">${percentage}%</span>` : ''}
            </div>
            <div class="progress">
                <div class="${progressClasses}" role="progressbar" 
                     style="width: ${percentage}%" 
                     aria-valuenow="${value}" 
                     aria-valuemin="0" 
                     aria-valuemax="${max}">
                </div>
            </div>
        `;
        
        return container;
    }
    
    generateProgressId() {
        return 'progress_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// ===== MAIN USER FEEDBACK CLASS =====

class UserFeedback {
    constructor() {
        this.loading = new LoadingStateManager();
        this.toast = new ToastManager();
        this.emptyState = new EmptyStateManager();
        this.progress = new ProgressIndicator();
    }
    
    // Convenience methods that combine multiple feedback types
    
    async handleAsyncOperation(operation, options = {}) {
        const {
            loadingTarget = 'global',
            loadingMessage = 'Procesando...',
            successMessage = 'Operación completada exitosamente',
            errorMessage = 'Ha ocurrido un error',
            showSuccessToast = true,
            showErrorToast = true
        } = options;
        
        const loaderId = this.loading.showLoading(loadingTarget, loadingMessage);
        
        try {
            const result = await operation();
            
            if (showSuccessToast) {
                this.toast.success(successMessage);
            }
            
            return result;
        } catch (error) {
            if (showErrorToast) {
                this.toast.error(errorMessage);
            }
            throw error;
        } finally {
            this.loading.hideLoading(loaderId);
        }
    }
    
    handleFormSubmission(form, submitFunction, options = {}) {
        const {
            successMessage = 'Formulario enviado exitosamente',
            errorMessage = 'Error al enviar el formulario'
        } = options;
        
        return this.handleAsyncOperation(submitFunction, {
            loadingTarget: form.querySelector('button[type="submit"]'),
            loadingMessage: 'Enviando...',
            successMessage: successMessage,
            errorMessage: errorMessage
        });
    }
    
    handleDataLoad(container, loadFunction, options = {}) {
        const {
            emptyStateConfig = {},
            errorMessage = 'Error al cargar los datos'
        } = options;
        
        return this.handleAsyncOperation(async () => {
            const data = await loadFunction();
            
            if (!data || (Array.isArray(data) && data.length === 0)) {
                this.emptyState.show(container, emptyStateConfig);
            }
            
            return data;
        }, {
            loadingTarget: container,
            loadingMessage: 'Cargando datos...',
            successMessage: null, // Don't show success toast for data loading
            errorMessage: errorMessage,
            showSuccessToast: false
        });
    }
}

// ===== INITIALIZATION =====

// Initialize user feedback system when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (!window.userFeedback) {
        window.userFeedback = new UserFeedback();
    }
    
    // Make individual managers available globally
    window.loadingManager = window.userFeedback.loading;
    window.toastManager = window.userFeedback.toast;
    window.emptyStateManager = window.userFeedback.emptyState;
    window.progressManager = window.userFeedback.progress;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        UserFeedback,
        LoadingStateManager,
        ToastManager,
        EmptyStateManager,
        ProgressIndicator
    };
}