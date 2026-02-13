/**
 * Gestor del árbol de taxonomía jerárquica
 * Maneja la interacción, búsqueda y navegación del árbol
 */

class TaxonomyTree {
    constructor(options = {}) {
        this.container = options.container || '#taxonomy-tree';
        this.searchUrl = options.searchUrl;
        this.treeDataUrl = options.treeDataUrl;
        this.nodeActionUrl = options.nodeActionUrl;
        this.csrfToken = options.csrfToken;
        
        this.selectedNode = null;
        this.expandedNodes = new Set();
        this.searchResults = [];
        this.currentFilters = {};
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialState();
    }
    
    bindEvents() {
        const container = document.querySelector(this.container);
        if (!container) return;
        
        // Eventos de clic en nodos
        container.addEventListener('click', (e) => {
            this.handleNodeClick(e);
        });
        
        // Eventos de teclado para navegación
        container.addEventListener('keydown', (e) => {
            this.handleKeyNavigation(e);
        });
        
        // Eventos de botones de acción
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]')) {
                this.handleAction(e.target.dataset.action, e.target);
            }
        });
    }
    
    handleNodeClick(e) {
        const nodeContent = e.target.closest('.node-content');
        if (!nodeContent) return;
        
        const nodeElement = nodeContent.closest('.tree-node');
        const nodeId = nodeElement.dataset.nodeId;
        const nodeType = nodeElement.dataset.nodeType;
        
        // Si se hizo clic en el toggle, expandir/colapsar
        if (e.target.closest('.node-toggle')) {
            this.toggleNode(nodeElement);
            return;
        }
        
        // Si se hizo clic en una acción, no seleccionar el nodo
        if (e.target.closest('.node-actions')) {
            return;
        }
        
        // Seleccionar el nodo
        this.selectNode(nodeElement, nodeId, nodeType);
    }
    
    toggleNode(nodeElement) {
        const nodeId = nodeElement.dataset.nodeId;
        const toggle = nodeElement.querySelector('.node-toggle');
        const children = nodeElement.querySelector('.node-children');
        
        if (!children) return;
        
        const isExpanded = this.expandedNodes.has(nodeId);
        
        if (isExpanded) {
            // Colapsar
            children.style.display = 'none';
            toggle.classList.remove('expanded');
            this.expandedNodes.delete(nodeId);
        } else {
            // Expandir
            children.style.display = 'block';
            toggle.classList.add('expanded');
            this.expandedNodes.add(nodeId);
            
            // Cargar datos si es necesario
            this.loadNodeChildren(nodeElement);
        }
        
        this.saveExpandedState();
    }
    
    selectNode(nodeElement, nodeId, nodeType) {
        // Remover selección anterior
        const previousSelected = document.querySelector('.node-content.selected');
        if (previousSelected) {
            previousSelected.classList.remove('selected');
        }
        
        // Seleccionar nuevo nodo
        const nodeContent = nodeElement.querySelector('.node-content');
        nodeContent.classList.add('selected');
        
        this.selectedNode = { id: nodeId, type: nodeType, element: nodeElement };
        
        // Cargar detalles del nodo
        this.loadNodeDetails(nodeId, nodeType);
        
        // Actualizar breadcrumbs
        this.updateBreadcrumbs(nodeElement);
    }
    
    async loadNodeDetails(nodeId, nodeType) {
        const detailsContainer = document.getElementById('node-details-container');
        if (!detailsContainer) return;
        
        try {
            detailsContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm"></div></div>';
            
            const response = await fetch(this.nodeActionUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.csrfToken
                },
                body: new URLSearchParams({
                    action: 'get_details',
                    node_id: nodeId,
                    node_type: nodeType
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.renderNodeDetails(data.data, nodeType);
            } else {
                throw new Error(data.error || 'Error al cargar detalles');
            }
            
        } catch (error) {
            console.error('Error loading node details:', error);
            detailsContainer.innerHTML = `
                <div class="text-center text-danger py-3">
                    <i class="bi bi-exclamation-triangle"></i>
                    <p class="mt-2 mb-0">Error al cargar detalles</p>
                </div>
            `;
        }
    }
    
    renderNodeDetails(data, nodeType) {
        const detailsContainer = document.getElementById('node-details-container');
        
        const typeIcons = {
            system: 'bi-diagram-2',
            subsystem: 'bi-diagram-3',
            group: 'bi-collection'
        };
        
        const typeColors = {
            system: 'text-primary',
            subsystem: 'text-success',
            group: 'text-info'
        };
        
        const typeLabels = {
            system: 'Sistema',
            subsystem: 'Subsistema',
            group: 'Grupo'
        };
        
        const statusBadge = data.is_active 
            ? '<span class="badge bg-success"><i class="bi bi-check-circle"></i> Activo</span>'
            : '<span class="badge bg-warning"><i class="bi bi-pause-circle"></i> Inactivo</span>';
        
        detailsContainer.innerHTML = `
            <div class="node-details-card">
                <div class="node-details-header">
                    <div class="node-details-icon ${typeColors[nodeType]}">
                        <i class="bi ${typeIcons[nodeType]}"></i>
                    </div>
                    <div>
                        <h6 class="node-details-title">${data.name}</h6>
                        <div class="mt-1">
                            <span class="badge bg-secondary">${data.code}</span>
                            ${statusBadge}
                        </div>
                    </div>
                </div>
                
                <div class="node-details-body">
                    <div class="node-details-row">
                        <span class="node-details-label">Tipo:</span>
                        <span class="node-details-value">${typeLabels[nodeType]}</span>
                    </div>
                    
                    ${data.description ? `
                        <div class="node-details-row">
                            <span class="node-details-label">Descripción:</span>
                            <span class="node-details-value">${data.description}</span>
                        </div>
                    ` : ''}
                    
                    ${data.sort_order !== undefined ? `
                        <div class="node-details-row">
                            <span class="node-details-label">Orden:</span>
                            <span class="node-details-value">${data.sort_order}</span>
                        </div>
                    ` : ''}
                    
                    <div class="node-details-row">
                        <span class="node-details-label">Creado:</span>
                        <span class="node-details-value">${new Date(data.created_at).toLocaleDateString()}</span>
                    </div>
                    
                    <div class="node-details-row">
                        <span class="node-details-label">Modificado:</span>
                        <span class="node-details-value">${new Date(data.updated_at).toLocaleDateString()}</span>
                    </div>
                    
                    ${this.renderChildrenCount(data, nodeType)}
                </div>
                
                <div class="mt-3">
                    <div class="btn-group w-100" role="group">
                        <button type="button" class="btn btn-outline-primary btn-sm" 
                                data-action="edit-${nodeType}" data-${nodeType}-id="${data.id}">
                            <i class="bi bi-pencil"></i> Editar
                        </button>
                        <button type="button" class="btn btn-outline-info btn-sm" 
                                data-action="view-${nodeType}" data-${nodeType}-id="${data.id}">
                            <i class="bi bi-eye"></i> Ver
                        </button>
                        ${nodeType !== 'group' ? `
                            <button type="button" class="btn btn-outline-success btn-sm" 
                                    data-action="add-child" data-parent-id="${data.id}" data-parent-type="${nodeType}">
                                <i class="bi bi-plus"></i> Agregar
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    renderChildrenCount(data, nodeType) {
        let childrenInfo = '';
        
        if (nodeType === 'system' && data.subsystems_count !== undefined) {
            childrenInfo = `
                <div class="node-details-row">
                    <span class="node-details-label">Subsistemas:</span>
                    <span class="node-details-value">
                        <span class="badge bg-success">${data.subsystems_count}</span>
                    </span>
                </div>
            `;
        } else if (nodeType === 'subsystem' && data.groups_count !== undefined) {
            childrenInfo = `
                <div class="node-details-row">
                    <span class="node-details-label">Grupos:</span>
                    <span class="node-details-value">
                        <span class="badge bg-info">${data.groups_count}</span>
                    </span>
                </div>
            `;
        }
        
        return childrenInfo;
    }
    
    updateBreadcrumbs(nodeElement) {
        const breadcrumbs = [];
        let currentElement = nodeElement;
        
        while (currentElement && currentElement.classList.contains('tree-node')) {
            const nodeContent = currentElement.querySelector('.node-content');
            const title = nodeContent.querySelector('.node-title strong').textContent;
            const code = nodeContent.querySelector('.badge').textContent;
            
            breadcrumbs.unshift({
                title: title,
                code: code,
                type: currentElement.dataset.nodeType
            });
            
            // Buscar el nodo padre
            const parentChildren = currentElement.closest('.node-children');
            if (parentChildren) {
                currentElement = parentChildren.closest('.tree-node');
            } else {
                break;
            }
        }
        
        // Actualizar breadcrumbs en la UI si existe el contenedor
        const breadcrumbContainer = document.getElementById('taxonomy-breadcrumbs');
        if (breadcrumbContainer) {
            this.renderBreadcrumbs(breadcrumbContainer, breadcrumbs);
        }
    }
    
    renderBreadcrumbs(container, breadcrumbs) {
        const breadcrumbHtml = breadcrumbs.map((item, index) => {
            const isLast = index === breadcrumbs.length - 1;
            const typeIcons = {
                system: 'bi-diagram-2',
                subsystem: 'bi-diagram-3',
                group: 'bi-collection'
            };
            
            return `
                <li class="breadcrumb-item ${isLast ? 'active' : ''}">
                    <i class="bi ${typeIcons[item.type]}"></i>
                    ${item.title}
                    <small class="text-muted ms-1">(${item.code})</small>
                </li>
            `;
        }).join('');
        
        container.innerHTML = `<ol class="breadcrumb mb-0">${breadcrumbHtml}</ol>`;
    }
    
    async search(query) {
        if (!query || query.length < 2) {
            this.clearSearch();
            return;
        }
        
        try {
            const response = await fetch(`${this.searchUrl}?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.results) {
                this.searchResults = data.results;
                this.renderSearchResults(data.results);
                this.highlightSearchResults(query);
            }
            
        } catch (error) {
            console.error('Error searching taxonomy:', error);
        }
    }
    
    renderSearchResults(results) {
        const resultsContainer = document.getElementById('search-results');
        const resultsList = document.getElementById('search-results-list');
        
        if (!resultsContainer || !resultsList) return;
        
        if (results.length === 0) {
            resultsContainer.style.display = 'none';
            return;
        }
        
        resultsContainer.style.display = 'block';
        
        resultsList.innerHTML = results.map(result => `
            <div class="search-result-item" data-node-id="${result.id}" data-node-type="${result.type}">
                <div class="search-result-title">
                    <i class="bi ${this.getTypeIcon(result.type)} me-2"></i>
                    ${result.name}
                    <span class="badge bg-secondary ms-2">${result.code}</span>
                </div>
                <div class="search-result-path">${result.path || ''}</div>
                ${result.description ? `<div class="search-result-description">${result.description}</div>` : ''}
            </div>
        `).join('');
        
        // Agregar eventos de clic a los resultados
        resultsList.addEventListener('click', (e) => {
            const resultItem = e.target.closest('.search-result-item');
            if (resultItem) {
                const nodeId = resultItem.dataset.nodeId;
                const nodeType = resultItem.dataset.nodeType;
                this.navigateToNode(nodeId, nodeType);
            }
        });
    }
    
    getTypeIcon(type) {
        const icons = {
            system: 'bi-diagram-2',
            subsystem: 'bi-diagram-3',
            group: 'bi-collection'
        };
        return icons[type] || 'bi-circle';
    }
    
    highlightSearchResults(query) {
        const container = document.querySelector(this.container);
        if (!container) return;
        
        // Remover highlights anteriores
        container.querySelectorAll('.highlight').forEach(el => {
            const parent = el.parentNode;
            parent.replaceChild(document.createTextNode(el.textContent), el);
            parent.normalize();
        });
        
        // Agregar nuevos highlights
        const regex = new RegExp(`(${query})`, 'gi');
        const walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            if (regex.test(node.textContent)) {
                textNodes.push(node);
            }
        }
        
        textNodes.forEach(textNode => {
            const parent = textNode.parentNode;
            const highlightedHTML = textNode.textContent.replace(regex, '<span class="highlight">$1</span>');
            const wrapper = document.createElement('div');
            wrapper.innerHTML = highlightedHTML;
            
            while (wrapper.firstChild) {
                parent.insertBefore(wrapper.firstChild, textNode);
            }
            parent.removeChild(textNode);
        });
    }
    
    clearSearch() {
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
        
        // Remover highlights
        const container = document.querySelector(this.container);
        if (container) {
            container.querySelectorAll('.highlight').forEach(el => {
                const parent = el.parentNode;
                parent.replaceChild(document.createTextNode(el.textContent), el);
                parent.normalize();
            });
        }
        
        this.searchResults = [];
    }
    
    filter(filterType, value) {
        this.currentFilters[filterType] = value;
        this.applyFilters();
    }
    
    applyFilters() {
        const container = document.querySelector(this.container);
        if (!container) return;
        
        const nodes = container.querySelectorAll('.tree-node');
        
        nodes.forEach(node => {
            let visible = true;
            
            // Filtro por nivel
            if (this.currentFilters.level) {
                const nodeType = node.dataset.nodeType;
                if (nodeType !== this.currentFilters.level) {
                    visible = false;
                }
            }
            
            // Filtro por estado
            if (this.currentFilters.status !== undefined && this.currentFilters.status !== '') {
                const isActive = !node.querySelector('.node-content').classList.contains('inactive');
                const filterActive = this.currentFilters.status === 'true';
                if (isActive !== filterActive) {
                    visible = false;
                }
            }
            
            node.style.display = visible ? 'block' : 'none';
        });
    }
    
    async navigateToNode(nodeId, nodeType) {
        // Expandir el camino hacia el nodo
        await this.expandPathToNode(nodeId, nodeType);
        
        // Seleccionar el nodo
        const nodeElement = document.querySelector(`[data-node-id="${nodeId}"][data-node-type="${nodeType}"]`);
        if (nodeElement) {
            this.selectNode(nodeElement, nodeId, nodeType);
            
            // Scroll hacia el nodo
            nodeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    async expandPathToNode(nodeId, nodeType) {
        // Implementar lógica para expandir el camino hacia un nodo específico
        // Esto requeriría obtener la ruta completa desde la API
        try {
            const response = await fetch(`${this.treeDataUrl}?node_id=${nodeId}&get_path=true`);
            const data = await response.json();
            
            if (data.path) {
                // Expandir cada nodo en el camino
                for (const pathNode of data.path) {
                    const element = document.querySelector(`[data-node-id="${pathNode.id}"]`);
                    if (element && !this.expandedNodes.has(pathNode.id)) {
                        this.toggleNode(element);
                    }
                }
            }
        } catch (error) {
            console.error('Error expanding path to node:', error);
        }
    }
    
    handleAction(action, element) {
        switch (action) {
            case 'expand-all':
                this.expandAll();
                break;
            case 'collapse-all':
                this.collapseAll();
                break;
            case 'refresh-tree':
                this.refreshTree();
                break;
            case 'validate-hierarchy':
                this.validateHierarchy(element);
                break;
            case 'create-subsystem':
                this.handleCreateSubsystem(element);
                break;
            case 'create-group':
                this.handleCreateGroup(element);
                break;
            case 'show-statistics':
                this.showStatistics();
                break;
            default:
                console.log('Unhandled action:', action);
        }
    }
    
    handleCreateSubsystem(element) {
        // Si hay un sistema seleccionado, redirigir a crear subsistema para ese sistema
        if (this.selectedNode && this.selectedNode.type === 'system') {
            const systemId = this.selectedNode.id;
            window.location.href = `/catalog/taxonomy/systems/${systemId}/subsystems/create/`;
        } else {
            // Si no hay sistema seleccionado, mostrar mensaje o ir a la lista
            if (confirm('Necesita seleccionar un sistema primero. ¿Desea ver la lista de sistemas?')) {
                window.location.href = '/catalog/taxonomy/systems/';
            }
        }
    }
    
    handleCreateGroup(element) {
        // Si hay un subsistema seleccionado, redirigir a crear grupo para ese subsistema
        if (this.selectedNode && this.selectedNode.type === 'subsystem') {
            const subsystemId = this.selectedNode.id;
            window.location.href = `/catalog/taxonomy/subsystems/${subsystemId}/groups/create/`;
        } else {
            // Si no hay subsistema seleccionado, mostrar mensaje
            if (confirm('Necesita seleccionar un subsistema primero. ¿Desea ver la lista de subsistemas?')) {
                window.location.href = '/catalog/taxonomy/systems/';
            }
        }
    }
    
    showStatistics() {
        // Mostrar estadísticas en un modal o alerta
        const statsContainer = document.querySelector('.row.mb-4');
        if (statsContainer) {
            // Scroll suave hacia las estadísticas
            statsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            // Resaltar las tarjetas de estadísticas
            const cards = statsContainer.querySelectorAll('.card');
            cards.forEach((card, index) => {
                card.style.transition = 'all 0.3s ease';
                card.style.transform = 'scale(1.05)';
                card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
                
                setTimeout(() => {
                    card.style.transform = 'scale(1)';
                    card.style.boxShadow = '';
                }, 500 + (index * 100));
            });
        }
    }
    
    expandAll() {
        const nodes = document.querySelectorAll('.tree-node');
        nodes.forEach(node => {
            const children = node.querySelector('.node-children');
            if (children && children.style.display === 'none') {
                this.toggleNode(node);
            }
        });
    }
    
    collapseAll() {
        const nodes = document.querySelectorAll('.tree-node');
        nodes.forEach(node => {
            const children = node.querySelector('.node-children');
            if (children && children.style.display !== 'none') {
                this.toggleNode(node);
            }
        });
    }
    
    async refreshTree() {
        const container = document.querySelector(this.container);
        if (!container) return;
        
        try {
            container.innerHTML = '<div class="text-center py-4"><div class="spinner-border"></div></div>';
            
            const response = await fetch(this.treeDataUrl);
            const data = await response.json();
            
            // Recargar la página para obtener el HTML actualizado
            window.location.reload();
            
        } catch (error) {
            console.error('Error refreshing tree:', error);
            container.innerHTML = '<div class="text-center text-danger py-4">Error al actualizar el árbol</div>';
        }
    }
    
    async validateHierarchy(buttonElement) {
        const button = buttonElement || document.querySelector('[data-action="validate-hierarchy"]');
        const originalText = button ? button.innerHTML : '';
        
        try {
            // Mostrar indicador de carga
            if (button) {
                button.disabled = true;
                button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Validando...';
            }
            
            // Intentar usar endpoint de validación (si existe)
            let response;
            try {
                response = await fetch('/api/v1/catalog/taxonomy/validate/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.csrfToken
                    }
                });
                
                if (!response.ok && response.status === 404) {
                    throw new Error('Endpoint no encontrado');
                }
            } catch (e) {
                // Si el endpoint no existe, hacer validación básica en el cliente
                const stats = document.querySelectorAll('.card.bg-primary, .card.bg-success, .card.bg-info, .card.bg-warning');
                let systemsCount = 0, subsystemsCount = 0, groupsCount = 0;
                
                stats.forEach(card => {
                    const title = card.querySelector('.card-title')?.textContent?.trim();
                    const count = parseInt(card.querySelector('h3')?.textContent?.trim() || '0');
                    
                    if (title?.includes('Sistemas')) systemsCount = count;
                    else if (title?.includes('Subsistemas')) subsystemsCount = count;
                    else if (title?.includes('Grupos')) groupsCount = count;
                });
                
                if (button) {
                    button.disabled = false;
                    button.innerHTML = originalText;
                }
                
                const message = `📊 Estadísticas de Taxonomía:\n\n` +
                    `• Sistemas: ${systemsCount}\n` +
                    `• Subsistemas: ${subsystemsCount}\n` +
                    `• Grupos: ${groupsCount}\n` +
                    `• Total: ${systemsCount + subsystemsCount + groupsCount}\n\n` +
                    `La estructura parece estar correcta. Para una validación completa, verifique que todos los subsistemas tengan un sistema padre y todos los grupos tengan un subsistema padre.`;
                
                alert(message);
                return;
            }
            
            const data = await response.json();
            
            if (data.is_valid) {
                alert('✅ La jerarquía de taxonomía es válida.');
            } else {
                const errors = data.errors || data.message || ['Errores encontrados en la jerarquía'];
                alert(`⚠️ Se encontraron problemas en la jerarquía:\n\n${errors.join('\n')}`);
            }
            
        } catch (error) {
            console.error('Error validating hierarchy:', error);
            alert('⚠️ No se pudo validar la jerarquía. Por favor, verifique la conexión con el servidor.');
        } finally {
            if (button) {
                button.disabled = false;
                button.innerHTML = originalText;
            }
        }
    }
    
    handleKeyNavigation(e) {
        if (!this.selectedNode) return;
        
        switch (e.key) {
            case 'ArrowUp':
                e.preventDefault();
                this.selectPreviousNode();
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.selectNextNode();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.expandSelectedNode();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.collapseSelectedNode();
                break;
            case 'Enter':
                e.preventDefault();
                this.activateSelectedNode();
                break;
        }
    }
    
    selectPreviousNode() {
        // Implementar navegación hacia arriba
    }
    
    selectNextNode() {
        // Implementar navegación hacia abajo
    }
    
    expandSelectedNode() {
        if (this.selectedNode && !this.expandedNodes.has(this.selectedNode.id)) {
            this.toggleNode(this.selectedNode.element);
        }
    }
    
    collapseSelectedNode() {
        if (this.selectedNode && this.expandedNodes.has(this.selectedNode.id)) {
            this.toggleNode(this.selectedNode.element);
        }
    }
    
    activateSelectedNode() {
        // Implementar activación del nodo seleccionado
    }
    
    loadInitialState() {
        // Cargar estado expandido desde localStorage
        const savedState = localStorage.getItem('taxonomy-tree-expanded');
        if (savedState) {
            try {
                const expandedIds = JSON.parse(savedState);
                expandedIds.forEach(id => {
                    const node = document.querySelector(`[data-node-id="${id}"]`);
                    if (node) {
                        this.expandedNodes.add(id);
                        const children = node.querySelector('.node-children');
                        const toggle = node.querySelector('.node-toggle');
                        if (children) {
                            children.style.display = 'block';
                            toggle.classList.add('expanded');
                        }
                    }
                });
            } catch (error) {
                console.error('Error loading expanded state:', error);
            }
        }
    }
    
    saveExpandedState() {
        localStorage.setItem('taxonomy-tree-expanded', JSON.stringify([...this.expandedNodes]));
    }
    
    async loadNodeChildren(nodeElement) {
        const nodeId = nodeElement.dataset.nodeId;
        const nodeType = nodeElement.dataset.nodeType;
        const childrenContainer = nodeElement.querySelector('.node-children');
        
        if (!childrenContainer || childrenContainer.dataset.loaded === 'true') {
            return;
        }
        
        try {
            nodeElement.classList.add('node-loading');
            
            const response = await fetch(`${this.treeDataUrl}?node_id=${nodeId}&node_type=${nodeType}`);
            const data = await response.json();
            
            if (data.children && data.children.length > 0) {
                // Renderizar hijos dinámicamente si es necesario
                // Por ahora, asumimos que los hijos ya están en el HTML
            }
            
            childrenContainer.dataset.loaded = 'true';
            
        } catch (error) {
            console.error('Error loading node children:', error);
        } finally {
            nodeElement.classList.remove('node-loading');
        }
    }
}

// Instancia global
window.TaxonomyTree = {
    instance: null,
    
    init: function(options) {
        this.instance = new TaxonomyTree(options);
        return this.instance;
    },
    
    search: function(query) {
        if (this.instance) {
            this.instance.search(query);
        }
    },
    
    filter: function(type, value) {
        if (this.instance) {
            this.instance.filter(type, value);
        }
    },
    
    clearSearch: function() {
        if (this.instance) {
            this.instance.clearSearch();
        }
    },
    
    navigateToNode: function(nodeId, nodeType) {
        if (this.instance) {
            this.instance.navigateToNode(nodeId, nodeType);
        }
    }
};