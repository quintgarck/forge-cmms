/**
 * MovIAx Theme Switcher
 * Sagecores - Sistema de Gestión Integral
 * Maneja el cambio entre modo claro y oscuro
 */

(function() {
    'use strict';

    const THEME_KEY = 'moviax-theme';
    const THEME_LIGHT = 'light';
    const THEME_DARK = 'dark';

    class ThemeSwitcher {
        constructor() {
            this.currentTheme = this.getStoredTheme() || this.getPreferredTheme();
            this.init();
        }

        /**
         * Inicializa el theme switcher
         */
        init() {
            // Aplicar tema inicial sin transición
            document.documentElement.classList.add('no-transition');
            this.applyTheme(this.currentTheme);
            
            // Remover clase no-transition después de un frame
            requestAnimationFrame(() => {
                document.documentElement.classList.remove('no-transition');
            });

            // Configurar event listeners
            this.setupEventListeners();

            // Escuchar cambios en preferencias del sistema
            this.watchSystemTheme();
            
// Navbar styling handled by NavbarThemeHandler
        }

        /**
         * Obtiene el tema almacenado en localStorage
         */
        getStoredTheme() {
            return localStorage.getItem(THEME_KEY);
        }

        /**
         * Obtiene el tema preferido del sistema
         */
        getPreferredTheme() {
            // SIEMPRE iniciar en modo claro por defecto
            return THEME_LIGHT;
        }

        /**
         * Guarda el tema en localStorage
         */
        storeTheme(theme) {
            localStorage.setItem(THEME_KEY, theme);
        }

        /**
         * Aplica el tema al documento
         */
        applyTheme(theme) {
            this.currentTheme = theme;
            
            if (theme === THEME_DARK) {
                document.documentElement.setAttribute('data-theme', 'dark');
                // Cambiar navbar a oscuro
                const navbar = document.getElementById('main-navbar');
                if (navbar) {
                    navbar.style.setProperty('background-color', '#0F172A', 'important');
                    navbar.classList.remove('bg-primary');
                    navbar.classList.add('bg-dark');
                }
            } else {
                document.documentElement.removeAttribute('data-theme');
                // Cambiar navbar a azul
                const navbar = document.getElementById('main-navbar');
                if (navbar) {
                    navbar.style.setProperty('background-color', '#2563EB', 'important');
                    navbar.classList.remove('bg-dark');
                    navbar.classList.add('bg-primary');
                }
            }

            this.updateToggleButton();
            this.storeTheme(theme);
            
            // Navbar styling is now handled by NavbarThemeHandler
            // Trigger themeChanged event for other components
            window.dispatchEvent(new CustomEvent('themeChanged', { 
                detail: { theme: theme } 
            }));

            // Disparar evento personalizado
            window.dispatchEvent(new CustomEvent('themeChanged', { 
                detail: { theme: theme } 
            }));
        }
        
// Navbar styling is now handled by NavbarThemeHandler

        /**
         * Alterna entre temas
         */
        toggleTheme() {
            const newTheme = this.currentTheme === THEME_LIGHT ? THEME_DARK : THEME_LIGHT;
            this.applyTheme(newTheme);
        }

        /**
         * Actualiza el botón de toggle
         */
        updateToggleButton() {
            const toggleBtn = document.getElementById('theme-toggle');
            const toggleIcon = document.getElementById('theme-icon');
            
            if (!toggleBtn || !toggleIcon) return;

            if (this.currentTheme === THEME_DARK) {
                toggleIcon.className = 'bi bi-sun-fill';
                toggleBtn.setAttribute('aria-label', 'Cambiar a modo claro');
                toggleBtn.setAttribute('title', 'Modo claro');
            } else {
                toggleIcon.className = 'bi bi-moon-stars-fill';
                toggleBtn.setAttribute('aria-label', 'Cambiar a modo oscuro');
                toggleBtn.setAttribute('title', 'Modo oscuro');
            }
        }

        /**
         * Configura los event listeners
         */
        setupEventListeners() {
            const toggleBtn = document.getElementById('theme-toggle');
            
            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => {
                    this.toggleTheme();
                    
                    // Animación de feedback
                    toggleBtn.style.transform = 'scale(0.9)';
                    setTimeout(() => {
                        toggleBtn.style.transform = 'scale(1)';
                    }, 150);
                });
            }

            // Atajo de teclado: Ctrl/Cmd + Shift + D
            document.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        }

        /**
         * Observa cambios en las preferencias del sistema
         */
        watchSystemTheme() {
            if (!window.matchMedia) return;

            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            // Usar el método correcto según disponibilidad
            if (darkModeQuery.addEventListener) {
                darkModeQuery.addEventListener('change', (e) => {
                    // Solo aplicar si no hay preferencia guardada
                    if (!this.getStoredTheme()) {
                        this.applyTheme(e.matches ? THEME_DARK : THEME_LIGHT);
                    }
                });
            } else if (darkModeQuery.addListener) {
                // Fallback para navegadores antiguos
                darkModeQuery.addListener((e) => {
                    if (!this.getStoredTheme()) {
                        this.applyTheme(e.matches ? THEME_DARK : THEME_LIGHT);
                    }
                });
            }
        }

        /**
         * Obtiene el tema actual
         */
        getCurrentTheme() {
            return this.currentTheme;
        }

        /**
         * Establece un tema específico
         */
        setTheme(theme) {
            if (theme === THEME_LIGHT || theme === THEME_DARK) {
                this.applyTheme(theme);
            }
        }
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.themeSwitcher = new ThemeSwitcher();
        });
    } else {
        window.themeSwitcher = new ThemeSwitcher();
    }

    // Exponer API global
    window.MovIAx = window.MovIAx || {};
    window.MovIAx.theme = {
        toggle: () => window.themeSwitcher.toggleTheme(),
        set: (theme) => window.themeSwitcher.setTheme(theme),
        get: () => window.themeSwitcher.getCurrentTheme(),
        isLight: () => window.themeSwitcher.getCurrentTheme() === THEME_LIGHT,
        isDark: () => window.themeSwitcher.getCurrentTheme() === THEME_DARK
    };

})();

/**
 * Utilidades adicionales para el tema
 */
window.MovIAx = window.MovIAx || {};

/**
 * Muestra una notificación toast
 */
window.MovIAx.showToast = function(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
};

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

/**
 * Log de cambios de tema (para debugging)
 */
window.addEventListener('themeChanged', (e) => {
    // Tema cambiado
});
