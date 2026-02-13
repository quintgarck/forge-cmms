/**
 * Navbar Theme Handler - Ensures navbar styling works correctly across theme changes
 * This is a dedicated handler to prevent navbar from becoming blank
 */

class NavbarThemeHandler {
    constructor() {
        this.navbar = null;
        this.observer = null;
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }
    
    setup() {
        this.navbar = document.getElementById('main-navbar');
        if (!this.navbar) {
            console.warn('[NavbarThemeHandler] Main navbar not found');
            return;
        }
        
        // Apply initial theme
        this.applyCurrentTheme();
        
        // Listen for theme changes
        window.addEventListener('themeChanged', () => {
            this.applyCurrentTheme();
        });
        
        // Setup mutation observer to catch external style changes
        this.setupMutationObserver();
        
        // Periodic check to ensure styles are maintained
        this.setupPeriodicCheck();
    }
    
    applyCurrentTheme() {
        if (!this.navbar) return;
        
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        
        // Clear all theme-related classes
        this.navbar.classList.remove(
            'bg-light', 'bg-white', 'bg-dark', 'bg-primary', 
            'navbar-light', 'navbar-dark'
        );
        
        // Handle container-fluid inside navbar
        const containerFluid = this.navbar.querySelector('.container-fluid');
        
        if (isDark) {
            // Dark mode styling
            this.navbar.classList.add('bg-dark', 'navbar-dark');
            this.navbar.style.setProperty('background-color', '#0F172A', 'important');
            
            // Apply dark mode to container-fluid
            if (containerFluid) {
                containerFluid.style.setProperty('background-color', 'transparent', 'important');
            }
            
            this.applyTextColor('#F8FAFC');
        } else {
            // Light mode styling
            this.navbar.classList.add('bg-primary', 'navbar-dark');
            this.navbar.style.setProperty('background-color', '#2563EB', 'important');
            
            // Apply light mode to container-fluid
            if (containerFluid) {
                containerFluid.style.setProperty('background-color', 'transparent', 'important');
            }
            
            this.applyTextColor('#FFFFFF');
        }
        
        console.log(`[NavbarThemeHandler] Applied ${isDark ? 'dark' : 'light'} theme`);
    }
    
    applyTextColor(color) {
        if (!this.navbar) return;
        
        // Target ALL elements in navbar to ensure complete styling
        const allNavbarElements = this.navbar.querySelectorAll('*');
        
        allNavbarElements.forEach(element => {
            // Apply text color to elements that typically contain text or icons
            if (element.nodeType === Node.ELEMENT_NODE) {
                const tagName = element.tagName.toLowerCase();
                const computedStyle = window.getComputedStyle(element);
                
                // Skip elements that shouldn't have text color forced
                if (tagName === 'script' || tagName === 'style' || tagName === 'meta') {
                    return;
                }
                
                // Force text color on text-containing elements
                if (computedStyle.color && computedStyle.color !== 'rgba(0, 0, 0, 0)') {
                    element.style.setProperty('color', color, 'important');
                }
                
                // Specifically target common navbar elements
                const commonSelectors = [
                    '.navbar-brand', '.nav-link', '.navbar-text', 'i', '.bi', '.btn',
                    '.dropdown-toggle', 'span', 'small', 'a', 'strong', 
                    '.navbar-nav .nav-link', '.navbar-toggler', '.navbar-toggler-icon',
                    '#theme-toggle', '#theme-icon', '.badge', '.dropdown-item'
                ];
                
                const selectorMatches = commonSelectors.some(selector => 
                    element.matches(selector)
                );
                
                if (selectorMatches) {
                    element.style.setProperty('color', color, 'important');
                }
            }
        });
        
        // Also handle pseudo-elements via dynamic CSS
        this.injectDynamicStyles(color);
    }
    
    injectDynamicStyles(textColor) {
        // Remove existing dynamic styles
        const existingStyle = document.getElementById('navbar-dynamic-styles');
        if (existingStyle) {
            existingStyle.remove();
        }
        
        // Create new dynamic styles
        const style = document.createElement('style');
        style.id = 'navbar-dynamic-styles';
        style.textContent = `
            #main-navbar .nav-link:hover,
            #main-navbar .nav-link:focus,
            #main-navbar .btn:hover,
            #main-navbar .dropdown-toggle:hover {
                color: ${textColor} !important;
                opacity: 0.8;
            }
            
            #main-navbar .navbar-brand:hover {
                color: ${textColor} !important;
                opacity: 0.9;
            }
            
            #main-navbar .navbar-toggler:focus {
                box-shadow: 0 0 0 0.25rem rgba(255, 255, 255, 0.25);
            }
        `;
        
        document.head.appendChild(style);
    }
    
    setupMutationObserver() {
        if (!this.navbar || !window.MutationObserver) return;
        
        this.observer = new MutationObserver((mutations) => {
            let shouldReapply = false;
            
            mutations.forEach(mutation => {
                // Check for class changes
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    shouldReapply = true;
                }
                
                // Check for style changes that might affect background
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    const bgColor = this.navbar.style.backgroundColor;
                    if (!bgColor || bgColor === 'white' || bgColor === 'transparent') {
                        shouldReapply = true;
                    }
                }
            });
            
            if (shouldReapply) {
                console.log('[NavbarThemeHandler] Detected unauthorized changes, reapplying theme');
                setTimeout(() => this.applyCurrentTheme(), 10);
            }
        });
        
        this.observer.observe(this.navbar, {
            attributes: true,
            attributeFilter: ['class', 'style'],
            subtree: false
        });
    }
    
    setupPeriodicCheck() {
        // Check every 500ms to ensure styles are maintained
        setInterval(() => {
            if (!this.navbar) return;
            
            const computedStyle = window.getComputedStyle(this.navbar);
            const bgColor = computedStyle.backgroundColor;
            
            // If background is white or transparent, reapply theme
            if (bgColor === 'rgba(0, 0, 0, 0)' || 
                bgColor === 'rgb(255, 255, 255)' || 
                bgColor === 'white') {
                console.log('[NavbarThemeHandler] Detected blank navbar, reapplying theme');
                this.applyCurrentTheme();
            }
        }, 500);
    }
    
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.navbarThemeHandler = new NavbarThemeHandler();
    });
} else {
    window.navbarThemeHandler = new NavbarThemeHandler();
}

// Export for global access
window.NavbarThemeHandler = NavbarThemeHandler;