/**
 * Enhanced Form Handler for ForgeDB Frontend
 * Provides comprehensive form validation, error handling, and user experience improvements
 */

class FormHandler {
    constructor(formSelector, options = {}) {
        this.form = document.querySelector(formSelector);
        this.options = {
            validateOnSubmit: true,
            validateOnBlur: true,
            showLoadingSpinner: true,
            scrollToErrors: true,
            autoSave: false,
            ...options
        };
        
        this.validators = new Map();
        this.isSubmitting = false;
        
        if (this.form) {
            this.init();
        }
    }
    
    init() {
        this.setupEventListeners();
        this.setupFieldValidation();
        
        if (this.options.autoSave) {
            this.setupAutoSave();
        }
    }
    
    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            if (this.options.validateOnSubmit) {
                if (!this.validateForm()) {
                    e.preventDefault();
                    this.handleValidationErrors();
                    return false;
                }
            }
            
            if (this.options.showLoadingSpinner) {
                this.showLoadingState();
            }
        });
        
        // Field validation on blur
        if (this.options.validateOnBlur) {
            const fields = this.form.querySelectorAll('input, select, textarea');
            fields.forEach(field => {
                field.addEventListener('blur', () => {
                    this.validateField(field);
                });
            });
        }
    }
    
    setupFieldValidation() {
        // Add default validators for common field types
        this.addValidator('email', this.validateEmail);
        this.addValidator('phone', this.validatePhone);
        this.addValidator('url', this.validateURL);
        this.addValidator('number', this.validateNumber);
    }
    
    addValidator(fieldName, validatorFunction) {
        this.validators.set(fieldName, validatorFunction);
    }
    
    validateField(field) {
        const fieldName = field.name || field.id;
        const validator = this.validators.get(fieldName);
        
        if (validator) {
            const result = validator(field);
            
            if (result.valid) {
                this.clearFieldError(field);
                this.setFieldState(field, 'valid');
            } else {
                this.showFieldError(field, result.message);
                this.setFieldState(field, 'invalid');
            }
            
            return result.valid;
        }
        
        return true;
    }
    
    validateForm() {
        let isValid = true;
        const fields = this.form.querySelectorAll('input, select, textarea');
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    showFieldError(field, message) {
        this.clearFieldError(field);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.innerHTML = `<i class="bi bi-exclamation-circle me-1"></i>${message}`;
        errorDiv.setAttribute('data-field-error', field.name || field.id);
        
        field.parentNode.appendChild(errorDiv);
        field.classList.add('is-invalid');
    }
    
    clearFieldError(field) {
        const existingError = field.parentNode.querySelector(`[data-field-error="${field.name || field.id}"]`);
        if (existingError) {
            existingError.remove();
        }
        
        field.classList.remove('is-invalid');
    }
    
    setFieldState(field, state) {
        field.classList.remove('is-valid', 'is-invalid');
        
        if (state === 'valid') {
            field.classList.add('is-valid');
        } else if (state === 'invalid') {
            field.classList.add('is-invalid');
        }
    }
    
    handleValidationErrors() {
        if (this.options.scrollToErrors) {
            const firstError = this.form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                firstError.focus();
            }
        }
        
        this.showToast('Por favor, corrija los errores en el formulario', 'error');
    }
    
    showLoadingState() {
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton) {
            this.isSubmitting = true;
            submitButton.disabled = true;
            
            const originalText = submitButton.innerHTML;
            submitButton.setAttribute('data-original-text', originalText);
            
            submitButton.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Procesando...
            `;
        }
    }
    
    hideLoadingState() {
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton && this.isSubmitting) {
            this.isSubmitting = false;
            submitButton.disabled = false;
            
            const originalText = submitButton.getAttribute('data-original-text');
            if (originalText) {
                submitButton.innerHTML = originalText;
            }
        }
    }
    
    setupAutoSave() {
        let saveTimer;
        const fields = this.form.querySelectorAll('input, select, textarea');
        
        fields.forEach(field => {
            field.addEventListener('input', () => {
                clearTimeout(saveTimer);
                saveTimer = setTimeout(() => {
                    this.saveDraft();
                }, 30000); // Save after 30 seconds of inactivity
            });
        });
    }
    
    saveDraft() {
        const formData = new FormData(this.form);
        const draftData = {};
        
        for (let [key, value] of formData.entries()) {
            if (key !== 'csrfmiddlewaretoken') {
                draftData[key] = value;
            }
        }
        
        const draftKey = `form_draft_${window.location.pathname}`;
        localStorage.setItem(draftKey, JSON.stringify(draftData));
        
        this.showToast('Borrador guardado automáticamente', 'info', 2000);
    }
    
    loadDraft() {
        const draftKey = `form_draft_${window.location.pathname}`;
        const draft = localStorage.getItem(draftKey);
        
        if (draft) {
            try {
                const draftData = JSON.parse(draft);
                let hasData = false;
                
                for (let [key, value] of Object.entries(draftData)) {
                    const field = this.form.querySelector(`[name="${key}"]`);
                    if (field && !field.value && value) {
                        field.value = value;
                        hasData = true;
                    }
                }
                
                if (hasData) {
                    this.showToast('Se ha restaurado un borrador guardado', 'success', 5000);
                }
            } catch (e) {
                console.warn('Error loading draft:', e);
            }
        }
    }
    
    clearDraft() {
        const draftKey = `form_draft_${window.location.pathname}`;
        localStorage.removeItem(draftKey);
    }
    
    showToast(message, type = 'info', duration = 3000) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${this.getBootstrapClass(type)} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${this.getIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        // Add to toast container or create one
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
    
    getBootstrapClass(type) {
        const classMap = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'primary'
        };
        return classMap[type] || 'primary';
    }
    
    getIcon(type) {
        const iconMap = {
            'success': 'check-circle',
            'error': 'exclamation-triangle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return iconMap[type] || 'info-circle';
    }
    
    // Default validators
    validateEmail(field) {
        const email = field.value.trim();
        if (!email) return { valid: true };
        
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return {
            valid: emailRegex.test(email),
            message: 'Ingrese un correo electrónico válido'
        };
    }
    
    validatePhone(field) {
        const phone = field.value.trim();
        if (!phone) return { valid: true };
        
        const digitsOnly = phone.replace(/\D/g, '');
        return {
            valid: digitsOnly.length >= 8 && digitsOnly.length <= 15,
            message: 'El teléfono debe tener entre 8 y 15 dígitos'
        };
    }
    
    validateURL(field) {
        const url = field.value.trim();
        if (!url) return { valid: true };
        
        try {
            new URL(url);
            return { valid: true };
        } catch {
            return {
                valid: false,
                message: 'Ingrese una URL válida'
            };
        }
    }
    
    validateNumber(field) {
        const value = field.value.trim();
        if (!value) return { valid: true };
        
        const number = parseFloat(value);
        return {
            valid: !isNaN(number),
            message: 'Ingrese un número válido'
        };
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormHandler;
} else {
    window.FormHandler = FormHandler;
}