/**
 * Taxonomy CRUD - Optimized JavaScript
 * MovIAx by Sagecores
 * Fecha: 31 de Enero 2026
 * 
 * Features:
 * - Debounced search
 * - Loading states
 * - Toast notifications
 * - Optimized AJAX calls
 * - Partial DOM updates
 */

(function() {
    'use strict';

    // ============================================================================
    // DEBOUNCE UTILITY
    // ============================================================================
    
    class DebounceUtil {
        constructor(callback, delay = 300) {
            this.callback = callback;
            this.delay = delay;
            this.timeout = null;
        }

        execute(...args) {
            clearTimeout(this.timeout);
            this.timeout = setTimeout(() => this.callback.apply(this, args), this.delay);
        }

        cancel() {
            clearTimeout(this.timeout);
        }
    }

    // ============================================================================
    // LOADING STATE MANAGER
    // ============================================================================
    
    class LoadingManager {
        constructor() {
            this.overlay = null;
            this.init();
        }

        init() {
            // Create global loader overlay
            this.overlay = document.createElement('div');
            this.overlay.className = 'global-loader-overlay';
            this.overlay.innerHTML = `
                <div class="spinner-container">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <div class="loading-text">Procesando...</div>
                </div>
            `;
            document.body.appendChild(this.overlay);
        }

        show(message = 'Procesando...') {
            const textElement = this.overlay.querySelector('.loading-text');
            if (textElement) textElement.textContent = message;
            this.overlay.classList.add('show');
        }

        hide() {
            this.overlay.classList.remove('show');
        }

        setButtonLoading(button, loading = true) {
            if (loading) {
                button.classList.add('btn-loading');
                button.dataset.originalText = button.innerHTML;
            } else {
                button.classList.remove('btn-loading');
            }
        }

        setRowLoading(rowId, loading = true) {
            const row = document.querySelector(`tr[data-system-id="${rowId}"]`);
            if (row) {
                if (loading) {
                    row.classList.add('tr-loading');
                } else {
                    row.classList.remove('tr-loading');
                }
            }
        }
    }

    // ============================================================================
    // TOAST NOTIFICATION SYSTEM
    // ============================================================================
    
    class ToastManager {
        constructor() {
            this.container = null;
            this.init();
        }

        init() {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }

        show(message, type = 'success', duration = 5000) {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type} align-items-center`;
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
            
            const iconMap = {
                success: 'check-circle-fill',
                error: 'x-circle-fill',
                warning: 'exclamation-triangle-fill',
                info: 'info-circle-fill'
            };
            
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-${iconMap[type]} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
                </div>
            `;
            
            this.container.appendChild(toast);
            
            const bsToast = new bootstrap.Toast(toast, { delay: duration });
            bsToast.show();
            
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        }

        success(message, duration) {
            this.show(message, 'success', duration);
        }

        error(message, duration = 8000) {
            this.show(message, 'error', duration);
        }

        warning(message, duration) {
            this.show(message, 'warning', duration);
        }

        info(message, duration) {
            this.show(message, 'info', duration);
        }
    }

    // ============================================================================
    // SEARCH WITH DEBOUNCE
    // ============================================================================
    
    class SearchManager {
        constructor(formSelector, inputSelector, delay = 300) {
            this.form = document.querySelector(formSelector);
            this.input = document.querySelector(inputSelector);
            this.debounceIndicator = null;
            this.debounceUtil = new DebounceUtil((value) => this.performSearch(value), delay);
            
            if (this.input) {
                this.init();
            }
        }

        init() {
            // Create debounce indicator
            this.debounceIndicator = document.createElement('div');
            this.debounceIndicator.className = 'search-debounce-indicator';
            this.debounceIndicator.innerHTML = `
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            `;
            this.input.parentElement.appendChild(this.debounceIndicator);

            // Bind events
            this.input.addEventListener('input', (e) => this.handleInput(e));
            this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
            
            // Clear button
            const clearBtn = this.input.parentElement.querySelector('.search-clear');
            if (clearBtn) {
                clearBtn.addEventListener('click', () => this.clearSearch());
            }
        }

        handleInput(e) {
            const value = e.target.value;
            
            // Show debounce indicator
            this.debounceIndicator.classList.add('show');
            
            // Execute debounced search
            this.debounceUtil.execute(value);
            
            // Update parent class for clear button
            if (value) {
                this.input.parentElement.classList.add('has-value');
            } else {
                this.input.parentElement.classList.remove('has-value');
            }
        }

        handleKeydown(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.debounceUtil.cancel();
                this.performSearch(this.input.value);
            } else if (e.key === 'Escape') {
                this.clearSearch();
            }
        }

        performSearch(value) {
            this.debounceIndicator.classList.remove('show');
            
            if (this.form) {
                // Show loading state
                window.loadingManager.show('Buscando...');
                
                // Submit form
                this.form.submit();
            }
        }

        clearSearch() {
            this.input.value = '';
            this.input.parentElement.classList.remove('has-value');
            this.input.focus();
            
            if (this.form) {
                window.loadingManager.show('Limpiando filtros...');
                this.form.submit();
            }
        }
    }

    // ============================================================================
    // TAXONOMY SYSTEM MANAGER
    // ============================================================================
    
    class TaxonomySystemManager {
        constructor() {
            this.loadingManager = window.loadingManager;
            this.toastManager = window.toastManager;
            this.init();
        }

        init() {
            this.bindEvents();
            this.initTooltips();
        }

        initTooltips() {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            [...tooltipTriggerList].map(tooltipTriggerEl => 
                new bootstrap.Tooltip(tooltipTriggerEl)
            );
        }

        bindEvents() {
            // Toggle status buttons
            document.addEventListener('click', (e) => {
                const toggleBtn = e.target.closest('[data-action="toggle-status"]');
                if (toggleBtn) {
                    e.preventDefault();
                    const systemId = toggleBtn.dataset.systemId;
                    this.toggleSystemStatus(systemId, toggleBtn);
                }
            });

            // Bulk actions
            document.addEventListener('click', (e) => {
                const bulkBtn = e.target.closest('[data-action^="bulk-"]');
                if (bulkBtn) {
                    e.preventDefault();
                    this.handleBulkAction(bulkBtn.dataset.action);
                }
            });

            // Select all checkbox
            const selectAllCheckbox = document.getElementById('select-all');
            const selectAllHeader = document.getElementById('select-all-header');
            
            [selectAllCheckbox, selectAllHeader].forEach(checkbox => {
                if (checkbox) {
                    checkbox.addEventListener('change', () => this.toggleSelectAll(checkbox.checked));
                }
            });

            // Individual checkboxes
            document.querySelectorAll('.row-select').forEach(checkbox => {
                checkbox.addEventListener('change', () => this.updateBulkActionsBar());
            });
        }

        toggleSelectAll(checked) {
            document.querySelectorAll('.row-select').forEach(cb => {
                cb.checked = checked;
            });
            this.updateBulkActionsBar();
        }

        updateBulkActionsBar() {
            const checkedCount = document.querySelectorAll('.row-select:checked').length;
            const bulkBar = document.querySelector('.bulk-actions-bar');
            
            if (bulkBar) {
                if (checkedCount > 0) {
                    bulkBar.classList.add('show');
                    bulkBar.querySelector('.selected-count').textContent = checkedCount;
                } else {
                    bulkBar.classList.remove('show');
                }
            }
        }

        async toggleSystemStatus(systemId, button) {
            // Show loading
            this.loadingManager.setRowLoading(systemId, true);
            button.classList.add('toggling');

            try {
                const response = await fetch(`/api/taxonomy-systems/${systemId}/toggle-active/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) throw new Error('Error en la respuesta');

                const data = await response.json();

                if (data.success) {
                    // Update row without reloading
                    this.updateRowStatus(systemId, data.is_active);
                    this.toastManager.success(`Estado actualizado exitosamente`);
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            } catch (error) {
                console.error('Error toggling status:', error);
                this.toastManager.error('Error al cambiar el estado: ' + error.message);
            } finally {
                this.loadingManager.setRowLoading(systemId, false);
                button.classList.remove('toggling');
            }
        }

        updateRowStatus(systemId, isActive) {
            const row = document.querySelector(`tr[data-system-id="${systemId}"]`);
            if (!row) return;

            // Update badge
            const badgeCell = row.querySelector('td:nth-child(6)');
            if (badgeCell) {
                const badge = badgeCell.querySelector('.badge');
                if (badge) {
                    badge.classList.add('status-changing');
                    
                    if (isActive) {
                        badge.className = 'badge bg-success';
                        badge.innerHTML = '<i class="bi bi-check-circle"></i> Activo';
                    } else {
                        badge.className = 'badge bg-warning';
                        badge.innerHTML = '<i class="bi bi-pause-circle"></i> Inactivo';
                    }
                    
                    setTimeout(() => badge.classList.remove('status-changing'), 500);
                }
            }

            // Update toggle button
            const toggleBtn = row.querySelector('[data-action="toggle-status"]');
            if (toggleBtn) {
                toggleBtn.title = isActive ? 'Desactivar' : 'Activar';
                toggleBtn.innerHTML = isActive ? 
                    '<i class="bi bi-pause"></i>' : 
                    '<i class="bi bi-play"></i>';
            }

            // Update row styling
            if (!isActive) {
                row.classList.add('table-secondary');
            } else {
                row.classList.remove('table-secondary');
            }
        }

        handleBulkAction(action) {
            const selectedIds = Array.from(document.querySelectorAll('.row-select:checked'))
                                    .map(cb => cb.value);
            
            if (selectedIds.length === 0) {
                this.toastManager.warning('Debe seleccionar al menos un sistema');
                return;
            }

            // Show confirmation modal
            const actionMap = {
                'bulk-activate': { text: 'activar', confirm: 'Los sistemas seleccionados serán activados.' },
                'bulk-deactivate': { text: 'desactivar', confirm: 'Los sistemas seleccionados serán desactivados.' },
                'bulk-delete': { text: 'eliminar', confirm: 'Los sistemas seleccionados serán eliminados permanentemente.' }
            };

            const actionInfo = actionMap[action];
            if (!actionInfo) return;

            if (action === 'bulk-export') {
                this.exportSystems(selectedIds);
                return;
            }

            // Show modal
            this.showBulkActionModal(action, actionInfo, selectedIds);
        }

        showBulkActionModal(action, actionInfo, selectedIds) {
            const modal = new bootstrap.Modal(document.getElementById('bulkActionModal'));
            
            document.querySelector('#bulkActionModal .modal-title').innerHTML = 
                `<i class="bi bi-gear"></i> ${actionInfo.text.charAt(0).toUpperCase() + actionInfo.text.slice(1)} Sistemas`;
            
            document.querySelector('#bulkActionModal .modal-body p').textContent = actionInfo.confirm;
            document.getElementById('selected-systems-list').innerHTML = 
                `<strong>${selectedIds.length}</strong> sistemas seleccionados`;

            const confirmBtn = document.getElementById('confirm-bulk-action');
            confirmBtn.onclick = () => {
                this.executeBulkAction(action, selectedIds);
                modal.hide();
            };

            modal.show();
        }

        async executeBulkAction(action, selectedIds) {
            this.loadingManager.show('Procesando sistemas seleccionados...');

            try {
                const formData = new FormData();
                formData.append('action', action);
                formData.append('selected_ids', selectedIds.join(','));
                formData.append('csrfmiddlewaretoken', this.getCsrfToken());

                const response = await fetch('/catalog/taxonomy/bulk-action/', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    this.toastManager.success(data.message);
                    
                    // Partial update for activate/deactivate
                    if (action === 'bulk-activate' || action === 'bulk-deactivate') {
                        selectedIds.forEach(id => {
                            this.updateRowStatus(id, action === 'bulk-activate');
                        });
                    } else {
                        // Reload for delete
                        setTimeout(() => location.reload(), 1500);
                    }
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            } catch (error) {
                console.error('Error in bulk action:', error);
                this.toastManager.error('Error: ' + error.message);
            } finally {
                this.loadingManager.hide();
            }
        }

        exportSystems(selectedIds) {
            const url = `/api/taxonomy-systems/export/?ids=${selectedIds.join(',')}`;
            window.open(url, '_blank');
            this.toastManager.success(`Exportando ${selectedIds.length} sistemas...`);
        }

        getCsrfToken() {
            const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
            return input ? input.value : '';
        }
    }

    // ============================================================================
    // INITIALIZE
    // ============================================================================
    
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize managers
        window.loadingManager = new LoadingManager();
        window.toastManager = new ToastManager();
        
        // Initialize search with debounce
        new SearchManager('form[method="get"]', '#search', 300);
        
        // Initialize taxonomy system manager
        new TaxonomySystemManager();
        
        console.log('Taxonomy CRUD Optimized - Loaded successfully');
    });

})();
