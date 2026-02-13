/**
 * ForgeDB Notification System
 * 
 * Advanced notification and alert management system with real-time updates,
 * filtering, categorization, and user interaction tracking.
 */

class NotificationSystem {
    constructor() {
        this.notifications = new Map();
        this.filters = {
            severity: 'all',
            category: 'all',
            read: 'all'
        };
        this.updateInterval = null;
        this.soundEnabled = true;
        this.maxNotifications = 50;
        
        this.init();
    }
    
    init() {
        this.createNotificationContainer();
        this.setupEventListeners();
        this.loadNotifications();
        this.startRealTimeUpdates();
    }
    
    createNotificationContainer() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }
        
        // Create notification dropdown content
        this.createNotificationDropdown();
    }
    
    createNotificationDropdown() {
        const notificationDropdown = document.getElementById('notification-dropdown');
        if (!notificationDropdown) return;
        
        notificationDropdown.innerHTML = `
            <div class="notification-header d-flex justify-content-between align-items-center p-3 border-bottom">
                <h6 class="mb-0">Notificaciones</h6>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="notificationSystem.markAllAsRead()">
                        <i class="bi bi-check-all"></i>
                    </button>
                    <button class="btn btn-outline-secondary" onclick="notificationSystem.clearAll()">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
            <div class="notification-filters p-2 border-bottom">
                <div class="row g-2">
                    <div class="col-4">
                        <select class="form-select form-select-sm" id="severity-filter">
                            <option value="all">Todas</option>
                            <option value="danger">Críticas</option>
                            <option value="warning">Advertencias</option>
                            <option value="info">Información</option>
                            <option value="success">Éxito</option>
                        </select>
                    </div>
                    <div class="col-4">
                        <select class="form-select form-select-sm" id="category-filter">
                            <option value="all">Categorías</option>
                            <option value="system">Sistema</option>
                            <option value="inventory">Inventario</option>
                            <option value="workorder">Órdenes</option>
                            <option value="client">Clientes</option>
                        </select>
                    </div>
                    <div class="col-4">
                        <select class="form-select form-select-sm" id="read-filter">
                            <option value="all">Estado</option>
                            <option value="unread">No leídas</option>
                            <option value="read">Leídas</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class="notification-list" id="notification-list" style="max-height: 400px; overflow-y: auto;">
                <div class="text-center p-4 text-muted">
                    <i class="bi bi-bell-slash display-4 opacity-50"></i>
                    <p class="mt-2">No hay notificaciones</p>
                </div>
            </div>
            <div class="notification-footer p-2 border-top">
                <a href="/notifications/" class="btn btn-sm btn-outline-primary w-100">
                    Ver todas las notificaciones
                </a>
            </div>
        `;
    }
    
    setupEventListeners() {
        // Filter change listeners
        document.addEventListener('change', (e) => {
            if (e.target.id === 'severity-filter') {
                this.filters.severity = e.target.value;
                this.renderNotifications();
            } else if (e.target.id === 'category-filter') {
                this.filters.category = e.target.value;
                this.renderNotifications();
            } else if (e.target.id === 'read-filter') {
                this.filters.read = e.target.value;
                this.renderNotifications();
            }
        });
        
        // Notification click handlers
        document.addEventListener('click', (e) => {
            if (e.target.closest('.notification-item')) {
                const notificationId = e.target.closest('.notification-item').dataset.notificationId;
                this.markAsRead(notificationId);
            }
            
            if (e.target.closest('.notification-dismiss')) {
                const notificationId = e.target.closest('.notification-item').dataset.notificationId;
                this.dismissNotification(notificationId);
            }
        });
        
        // Settings toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="toggle-sound"]')) {
                this.toggleSound();
            }
        });
    }
    
    async loadNotifications() {
        try {
            // TODO: Implement notifications API endpoint
            // For now, we'll use mock data or skip loading
            console.log('Notifications API not implemented yet - skipping load');
            
            // Optional: Add some mock notifications for testing
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                // Add mock notification only in development
                this.addNotification({
                    id: 'welcome',
                    title: 'Bienvenido a ForgeDB',
                    message: 'Sistema de gestión de taller automotriz',
                    severity: 'info',
                    category: 'system',
                    created_at: new Date().toISOString()
                }, false);
                this.renderNotifications();
                this.updateBadge();
            }
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }
    
    addNotification(notification, isNew = true) {
        // Ensure notification has required properties
        const fullNotification = {
            id: notification.id || Date.now().toString(),
            title: notification.title || 'Notificación',
            message: notification.message || '',
            severity: notification.severity || 'info',
            category: notification.category || 'system',
            created_at: notification.created_at || new Date().toISOString(),
            is_read: notification.is_read || false,
            actions: notification.actions || [],
            ...notification
        };
        
        this.notifications.set(fullNotification.id, fullNotification);
        
        // Limit number of notifications
        if (this.notifications.size > this.maxNotifications) {
            const oldestId = Array.from(this.notifications.keys())[0];
            this.notifications.delete(oldestId);
        }
        
        if (isNew) {
            this.showToast(fullNotification);
            this.playNotificationSound(fullNotification.severity);
            this.renderNotifications();
            this.updateBadge();
        }
    }
    
    showToast(notification) {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;
        
        const toastId = `toast-${notification.id}`;
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-bg-${notification.severity} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <div class="d-flex align-items-start">
                        <div class="flex-shrink-0 me-2">
                            <i class="bi bi-${this.getSeverityIcon(notification.severity)}"></i>
                        </div>
                        <div class="flex-grow-1">
                            <strong>${notification.title}</strong>
                            <div class="small">${notification.message}</div>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        if (typeof bootstrap === 'undefined') {
            console.error('Bootstrap is not loaded');
            return;
        }
        
        const bsToast = new bootstrap.Toast(toast, {
            delay: this.getToastDelay(notification.severity)
        });
        
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toastContainer.removeChild(toast);
        });
        
        // Mark as read when toast is clicked
        toast.addEventListener('click', () => {
            this.markAsRead(notification.id);
        });
    }
    
    renderNotifications() {
        const notificationList = document.getElementById('notification-list');
        if (!notificationList) return;
        
        const filteredNotifications = this.getFilteredNotifications();
        
        if (filteredNotifications.length === 0) {
            notificationList.innerHTML = `
                <div class="text-center p-4 text-muted">
                    <i class="bi bi-bell-slash display-4 opacity-50"></i>
                    <p class="mt-2">No hay notificaciones que coincidan con los filtros</p>
                </div>
            `;
            return;
        }
        
        const notificationsHTML = filteredNotifications.map(notification => {
            const timeAgo = this.getTimeAgo(notification.created_at);
            const isUnread = !notification.is_read;
            
            return `
                <div class="notification-item ${isUnread ? 'notification-unread' : ''}" 
                     data-notification-id="${notification.id}">
                    <div class="d-flex align-items-start p-3 border-bottom notification-content">
                        <div class="flex-shrink-0 me-3">
                            <div class="notification-icon bg-${notification.severity} text-white rounded-circle d-flex align-items-center justify-content-center" 
                                 style="width: 32px; height: 32px;">
                                <i class="bi bi-${this.getSeverityIcon(notification.severity)} small"></i>
                            </div>
                        </div>
                        <div class="flex-grow-1 min-width-0">
                            <div class="d-flex justify-content-between align-items-start">
                                <h6 class="notification-title mb-1 ${isUnread ? 'fw-bold' : ''}">${notification.title}</h6>
                                <div class="d-flex align-items-center">
                                    ${isUnread ? '<span class="badge bg-primary rounded-pill me-2">Nuevo</span>' : ''}
                                    <button class="btn btn-sm btn-outline-secondary notification-dismiss" 
                                            title="Descartar">
                                        <i class="bi bi-x"></i>
                                    </button>
                                </div>
                            </div>
                            <p class="notification-message mb-1 text-muted small">${notification.message}</p>
                            <div class="d-flex justify-content-between align-items-center">
                                <small class="text-muted">
                                    <i class="bi bi-clock me-1"></i>${timeAgo}
                                    <span class="mx-2">•</span>
                                    <span class="badge bg-light text-dark">${this.getCategoryName(notification.category)}</span>
                                </small>
                                ${notification.actions && notification.actions.length > 0 ? 
                                    `<div class="notification-actions">
                                        ${notification.actions.map(action => 
                                            `<button class="btn btn-sm btn-outline-primary me-1" 
                                                     onclick="notificationSystem.executeAction('${notification.id}', '${action.type}')">
                                                ${action.label}
                                            </button>`
                                        ).join('')}
                                    </div>` : ''
                                }
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        notificationList.innerHTML = notificationsHTML;
    }
    
    getFilteredNotifications() {
        let notifications = Array.from(this.notifications.values());
        
        // Sort by creation date (newest first)
        notifications.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        // Apply filters
        if (this.filters.severity !== 'all') {
            notifications = notifications.filter(n => n.severity === this.filters.severity);
        }
        
        if (this.filters.category !== 'all') {
            notifications = notifications.filter(n => n.category === this.filters.category);
        }
        
        if (this.filters.read !== 'all') {
            const isRead = this.filters.read === 'read';
            notifications = notifications.filter(n => n.is_read === isRead);
        }
        
        return notifications;
    }
    
    markAsRead(notificationId) {
        const notification = this.notifications.get(notificationId);
        if (notification && !notification.is_read) {
            notification.is_read = true;
            this.notifications.set(notificationId, notification);
            this.renderNotifications();
            this.updateBadge();
            
            // Send to server
            this.updateNotificationOnServer(notificationId, { is_read: true });
        }
    }
    
    markAllAsRead() {
        let hasChanges = false;
        this.notifications.forEach((notification, id) => {
            if (!notification.is_read) {
                notification.is_read = true;
                this.notifications.set(id, notification);
                hasChanges = true;
            }
        });
        
        if (hasChanges) {
            this.renderNotifications();
            this.updateBadge();
            
            // TODO: Send to server when notifications API is implemented
            console.log('Mark all as read - API call skipped (not implemented)');
        }
    }
    
    dismissNotification(notificationId) {
        this.notifications.delete(notificationId);
        this.renderNotifications();
        this.updateBadge();
        
        // TODO: Send to server when notifications API is implemented
        console.log(`Dismiss notification ${notificationId} - API call skipped (not implemented)`);
    }
    
    clearAll() {
        if (confirm('¿Estás seguro de que quieres eliminar todas las notificaciones?')) {
            this.notifications.clear();
            this.renderNotifications();
            this.updateBadge();
            
            // TODO: Send to server when notifications API is implemented
            console.log('Clear all notifications - API call skipped (not implemented)');
        }
    }
    
    executeAction(notificationId, actionType) {
        const notification = this.notifications.get(notificationId);
        if (!notification) return;
        
        const action = notification.actions.find(a => a.type === actionType);
        if (!action) return;
        
        // Execute action based on type
        switch (actionType) {
            case 'view':
                if (action.url) {
                    window.location.href = action.url;
                }
                break;
            case 'dismiss':
                this.dismissNotification(notificationId);
                break;
            case 'snooze':
                this.snoozeNotification(notificationId, action.duration || 3600000); // 1 hour default
                break;
            default:
                console.log(`Unknown action type: ${actionType}`);
        }
        
        // Mark as read after action
        this.markAsRead(notificationId);
    }
    
    snoozeNotification(notificationId, duration) {
        const notification = this.notifications.get(notificationId);
        if (!notification) return;
        
        // Hide notification temporarily
        notification.snoozed_until = new Date(Date.now() + duration).toISOString();
        this.notifications.set(notificationId, notification);
        this.renderNotifications();
        
        // Set timeout to show again
        setTimeout(() => {
            const snoozedNotification = this.notifications.get(notificationId);
            if (snoozedNotification) {
                delete snoozedNotification.snoozed_until;
                this.notifications.set(notificationId, snoozedNotification);
                this.renderNotifications();
                this.showToast(snoozedNotification);
            }
        }, duration);
    }
    
    updateBadge() {
        const unreadCount = Array.from(this.notifications.values())
            .filter(n => !n.is_read && !n.snoozed_until).length;
        
        const badge = document.getElementById('notification-badge');
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : unreadCount.toString();
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
        
        // Update document title
        if (unreadCount > 0) {
            document.title = `(${unreadCount}) ForgeDB - Dashboard`;
        } else {
            document.title = 'ForgeDB - Dashboard';
        }
    }
    
    startRealTimeUpdates() {
        // Poll for new notifications every 30 seconds
        this.updateInterval = setInterval(() => {
            this.checkForNewNotifications();
        }, 30000);
    }
    
    async checkForNewNotifications() {
        try {
            // TODO: Implement notifications API endpoint
            // For now, skip checking for new notifications
            console.log('Check for new notifications - API call skipped (not implemented)');
            localStorage.setItem('lastNotificationCheck', new Date().toISOString());
        } catch (error) {
            console.error('Failed to check for new notifications:', error);
        }
    }
    
    async updateNotificationOnServer(notificationId, updates) {
        try {
            // TODO: Implement notifications API endpoint
            console.log(`Update notification ${notificationId} - API call skipped (not implemented)`, updates);
        } catch (error) {
            console.error('Failed to update notification on server:', error);
        }
    }
    
    playNotificationSound(severity) {
        if (!this.soundEnabled) return;
        
        // Create audio element for notification sound
        const audio = new Audio();
        
        switch (severity) {
            case 'danger':
                audio.src = '/static/frontend/sounds/error.mp3';
                break;
            case 'warning':
                audio.src = '/static/frontend/sounds/warning.mp3';
                break;
            case 'success':
                audio.src = '/static/frontend/sounds/success.mp3';
                break;
            default:
                audio.src = '/static/frontend/sounds/notification.mp3';
        }
        
        audio.volume = 0.3;
        audio.play().catch(error => {
            // Ignore audio play errors (user interaction required)
            console.debug('Audio play failed:', error);
        });
    }
    
    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        localStorage.setItem('notificationSoundEnabled', this.soundEnabled.toString());
        
        const soundToggle = document.querySelector('[data-action="toggle-sound"]');
        if (soundToggle) {
            const icon = soundToggle.querySelector('i');
            if (icon) {
                icon.className = this.soundEnabled ? 'bi bi-volume-up' : 'bi bi-volume-mute';
            }
        }
        
        ForgeDB.utils.showToast(
            `Sonidos de notificación ${this.soundEnabled ? 'activados' : 'desactivados'}`,
            'info'
        );
    }
    
    // Utility methods
    getSeverityIcon(severity) {
        const icons = {
            'danger': 'exclamation-triangle-fill',
            'warning': 'exclamation-circle-fill',
            'info': 'info-circle-fill',
            'success': 'check-circle-fill'
        };
        return icons[severity] || 'bell-fill';
    }
    
    getCategoryName(category) {
        const names = {
            'system': 'Sistema',
            'inventory': 'Inventario',
            'workorder': 'Órdenes',
            'client': 'Clientes',
            'equipment': 'Equipos',
            'finance': 'Finanzas'
        };
        return names[category] || 'General';
    }
    
    getToastDelay(severity) {
        const delays = {
            'danger': 8000,
            'warning': 6000,
            'info': 4000,
            'success': 3000
        };
        return delays[severity] || 4000;
    }
    
    getTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return 'Hace un momento';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `Hace ${minutes} minuto${minutes > 1 ? 's' : ''}`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `Hace ${hours} hora${hours > 1 ? 's' : ''}`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `Hace ${days} día${days > 1 ? 's' : ''}`;
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    // Public API methods
    createNotification(title, message, severity = 'info', category = 'system', actions = []) {
        const notification = {
            id: Date.now().toString(),
            title,
            message,
            severity,
            category,
            actions,
            created_at: new Date().toISOString(),
            is_read: false
        };
        
        this.addNotification(notification, true);
        return notification.id;
    }
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        this.notifications.clear();
    }
}

// Initialize notification system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.notificationSystem = new NotificationSystem();
    
    // Load sound preference
    const soundEnabled = localStorage.getItem('notificationSoundEnabled');
    if (soundEnabled !== null) {
        window.notificationSystem.soundEnabled = soundEnabled === 'true';
    }
});

// Export for global use
window.NotificationSystem = NotificationSystem;