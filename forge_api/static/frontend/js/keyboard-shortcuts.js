/**
 * Sistema de atajos de teclado para ForgeDB
 */

(function() {
    'use strict';
    
    // Configuración de atajos de teclado
    const shortcuts = {
        // Navegación
        'ctrl+k': {
            action: 'openSearch',
            description: 'Búsqueda rápida',
            context: 'global'
        },
        'alt+arrowleft': {
            action: 'goBack',
            description: 'Página anterior',
            context: 'global'
        },
        'alt+arrowright': {
            action: 'goForward',
            description: 'Página siguiente',
            context: 'global'
        },
        
        // Acciones en listas
        'ctrl+n': {
            action: 'createNew',
            description: 'Crear nuevo elemento',
            context: 'list'
        },
        
        // Acciones en formularios
        'ctrl+s': {
            action: 'saveForm',
            description: 'Guardar cambios',
            context: 'form'
        },
        'ctrl+e': {
            action: 'editCurrent',
            description: 'Editar elemento actual',
            context: 'detail'
        },
        
        // Modales y diálogos
        'escape': {
            action: 'closeModal',
            description: 'Cerrar modal/diálogo',
            context: 'modal'
        },
        
        // Ayuda
        'shift+?': {
            action: 'showHelp',
            description: 'Mostrar ayuda de atajos',
            context: 'global'
        }
    };
    
    // Estado actual
    let currentContext = 'global';
    
    // Detectar contexto actual
    function detectContext() {
        if (document.querySelector('form')) {
            currentContext = 'form';
        } else if (document.querySelector('.modal.show')) {
            currentContext = 'modal';
        } else if (document.querySelector('[data-context="list"]')) {
            currentContext = 'list';
        } else if (document.querySelector('[data-context="detail"]')) {
            currentContext = 'detail';
        } else {
            currentContext = 'global';
        }
    }
    
    // Normalizar tecla presionada
    function normalizeKey(event) {
        let key = event.key.toLowerCase();
        const modifiers = [];
        
        if (event.ctrlKey) modifiers.push('ctrl');
        if (event.altKey) modifiers.push('alt');
        if (event.shiftKey) modifiers.push('shift');
        if (event.metaKey) modifiers.push('meta');
        
        if (modifiers.length > 0) {
            return modifiers.join('+') + '+' + key;
        }
        
        return key;
    }
    
    // Ejecutar acción según el atajo
    function executeShortcut(shortcutKey) {
        const shortcut = shortcuts[shortcutKey];
        
        if (!shortcut) return false;
        
        // Verificar contexto
        if (shortcut.context !== 'global' && shortcut.context !== currentContext) {
            return false;
        }
        
        // Ejecutar acción
        switch (shortcut.action) {
            case 'openSearch':
                openGlobalSearch();
                return true;
            
            case 'goBack':
                window.history.back();
                return true;
            
            case 'goForward':
                window.history.forward();
                return true;
            
            case 'createNew':
                const createBtn = document.querySelector('[data-action="create"]');
                if (createBtn) {
                    createBtn.click();
                    return true;
                }
                break;
            
            case 'saveForm':
                const form = document.querySelector('form');
                if (form) {
                    form.submit();
                    return true;
                }
                break;
            
            case 'editCurrent':
                const editBtn = document.querySelector('[data-action="edit"]');
                if (editBtn) {
                    editBtn.click();
                    return true;
                }
                break;
            
            case 'closeModal':
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                        return true;
                    }
                }
                break;
            
            case 'showHelp':
                showKeyboardShortcutsHelp();
                return true;
        }
        
        return false;
    }
    
    // Abrir búsqueda global
    function openGlobalSearch() {
        const searchInput = document.querySelector('#global-search-input');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        } else {
            // Crear modal de búsqueda si no existe
            createSearchModal();
        }
    }
    
    // Crear modal de búsqueda
    function createSearchModal() {
        const modalHTML = `
            <div class="modal fade" id="searchModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-search"></i> Búsqueda Rápida
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <input type="text" class="form-control form-control-lg" 
                                   id="global-search-input" 
                                   placeholder="Buscar en todo el sistema..."
                                   autofocus>
                            <div id="search-results" class="mt-3">
                                <!-- Resultados de búsqueda -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('searchModal'));
        modal.show();
    }
    
    // Mostrar ayuda de atajos de teclado
    function showKeyboardShortcutsHelp() {
        const helpHTML = `
            <div class="modal fade" id="shortcutsHelpModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-keyboard"></i> Atajos de Teclado
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Atajo</th>
                                            <th>Acción</th>
                                            <th>Contexto</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${Object.entries(shortcuts).map(([key, shortcut]) => `
                                            <tr>
                                                <td><kbd>${key.replace(/\+/g, '</kbd> + <kbd>')}</kbd></td>
                                                <td>${shortcut.description}</td>
                                                <td><span class="badge bg-secondary">${shortcut.context}</span></td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Eliminar modal anterior si existe
        const existingModal = document.getElementById('shortcutsHelpModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        document.body.insertAdjacentHTML('beforeend', helpHTML);
        const modal = new bootstrap.Modal(document.getElementById('shortcutsHelpModal'));
        modal.show();
    }
    
    // Event listener para teclas
    document.addEventListener('keydown', function(event) {
        // Ignorar si estamos en un input/textarea (excepto para atajos específicos)
        const activeElement = document.activeElement;
        const isInputField = activeElement.tagName === 'INPUT' || 
                           activeElement.tagName === 'TEXTAREA' ||
                           activeElement.isContentEditable;
        
        // Detectar contexto actual
        detectContext();
        
        // Normalizar tecla
        const key = normalizeKey(event);
        
        // Permitir ciertos atajos incluso en campos de entrada
        const allowedInInput = ['ctrl+s', 'escape', 'shift+?'];
        
        if (isInputField && !allowedInInput.includes(key)) {
            return;
        }
        
        // Ejecutar atajo
        if (executeShortcut(key)) {
            event.preventDefault();
            event.stopPropagation();
        }
    });
    
    // Mostrar indicador de atajo disponible
    function showShortcutHint(element, shortcutKey) {
        const hint = document.createElement('span');
        hint.className = 'keyboard-shortcut-hint';
        hint.textContent = shortcutKey;
        element.appendChild(hint);
    }
    
    // Inicializar indicadores de atajos
    document.addEventListener('DOMContentLoaded', function() {
        // Agregar indicadores visuales a botones con atajos
        const createBtn = document.querySelector('[data-action="create"]');
        if (createBtn) {
            createBtn.setAttribute('title', 'Ctrl+N para crear nuevo');
        }
        
        const editBtn = document.querySelector('[data-action="edit"]');
        if (editBtn) {
            editBtn.setAttribute('title', 'Ctrl+E para editar');
        }
        
        // Agregar botón de ayuda de atajos
        const helpButton = `
            <button type="button" class="btn btn-sm btn-outline-secondary position-fixed bottom-0 end-0 m-3" 
                    onclick="window.showKeyboardShortcutsHelp()" 
                    title="Atajos de teclado (Shift+?)">
                <i class="bi bi-keyboard"></i>
            </button>
        `;
        document.body.insertAdjacentHTML('beforeend', helpButton);
    });
    
    // Exportar funciones globales
    window.showKeyboardShortcutsHelp = showKeyboardShortcutsHelp;
    
})();
