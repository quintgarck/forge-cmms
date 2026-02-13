# Guía de Uso: Theme Switcher MovIAx

**Sistema:** MovIAx by Sagecores  
**Funcionalidad:** Cambio entre modo claro y oscuro  
**Versión:** 1.0.0

---

## 🎨 ¿Qué es el Theme Switcher?

El Theme Switcher es una funcionalidad que permite a los usuarios cambiar entre el modo claro (light) y el modo oscuro (dark) del sistema MovIAx, adaptándose a sus preferencias visuales y condiciones de iluminación.

---

## 🔘 Ubicación del Botón

El botón de cambio de tema se encuentra en la **barra de navegación superior**, en el lado derecho, justo antes de las notificaciones y el menú de usuario.

```
┌─────────────────────────────────────────────────────────┐
│ ☰ MovIAx by Sagecores    [🌙] [🔔] [👤 Usuario]       │
└─────────────────────────────────────────────────────────┘
                            ↑
                    Botón Theme Switcher
```

---

## 🖱️ Cómo Usar

### Método 1: Click en el Botón
1. Localiza el botón circular en la navbar superior
2. Haz click en el botón
3. El tema cambiará instantáneamente

**Iconos:**
- 🌙 **Luna:** Indica que estás en modo claro (click para cambiar a oscuro)
- ☀️ **Sol:** Indica que estás en modo oscuro (click para cambiar a claro)

### Método 2: Atajo de Teclado
Presiona: `Ctrl + Shift + D` (Windows/Linux) o `Cmd + Shift + D` (Mac)

---

## 🎨 Modos Disponibles

### Modo Claro (Light)
- **Fondo:** Blanco y tonos claros
- **Texto:** Negro y grises oscuros
- **Ideal para:** Ambientes bien iluminados, trabajo diurno
- **Colores:** Azul primario `#2563EB`, fondos blancos

### Modo Oscuro (Dark)
- **Fondo:** Negro y tonos oscuros
- **Texto:** Blanco y grises claros
- **Ideal para:** Ambientes con poca luz, trabajo nocturno, reducir fatiga visual
- **Colores:** Azul más claro `#3B82F6`, fondos oscuros

---

## 💾 Persistencia

Tu preferencia de tema se guarda automáticamente en tu navegador:
- ✅ Se mantiene al cerrar y abrir el navegador
- ✅ Se mantiene al navegar entre páginas
- ✅ Es específica para cada dispositivo/navegador

---

## 🔄 Detección Automática

El sistema detecta automáticamente las preferencias de tu sistema operativo:
- Si tu SO está en modo oscuro → MovIAx inicia en modo oscuro
- Si tu SO está en modo claro → MovIAx inicia en modo claro
- Si cambias las preferencias de tu SO, MovIAx se adapta automáticamente

**Nota:** Tu preferencia manual siempre tiene prioridad sobre la detección automática.

---

## 🎯 Elementos que Cambian

Cuando cambias de tema, los siguientes elementos se adaptan:

### Colores
- ✅ Fondos de página
- ✅ Fondos de tarjetas (cards)
- ✅ Colores de texto
- ✅ Bordes y separadores

### Componentes
- ✅ Navbar (barra de navegación)
- ✅ Sidebar (menú lateral)
- ✅ Formularios (inputs, selects)
- ✅ Tablas
- ✅ Modales
- ✅ Dropdowns
- ✅ Botones
- ✅ Alertas
- ✅ Badges
- ✅ Breadcrumbs
- ✅ Footer

### Gráficos
- ✅ Los gráficos de Chart.js se adaptan automáticamente
- ✅ Los colores de las series se ajustan para mejor contraste

---

## 🛠️ Para Desarrolladores

### API JavaScript

```javascript
// Cambiar tema manualmente
window.MovIAx.theme.toggle();

// Establecer tema específico
window.MovIAx.theme.set('dark');
window.MovIAx.theme.set('light');

// Obtener tema actual
const currentTheme = window.MovIAx.theme.get();
console.log(currentTheme); // 'light' o 'dark'

// Verificar tema actual
if (window.MovIAx.theme.isDark()) {
    console.log('Modo oscuro activo');
}

if (window.MovIAx.theme.isLight()) {
    console.log('Modo claro activo');
}
```

### Eventos Personalizados

```javascript
// Escuchar cambios de tema
window.addEventListener('themeChanged', (event) => {
    const newTheme = event.detail.theme;
    console.log(`Tema cambiado a: ${newTheme}`);
    
    // Ejecutar lógica personalizada
    if (newTheme === 'dark') {
        // Código para modo oscuro
    } else {
        // Código para modo claro
    }
});
```

### Variables CSS Personalizadas

```css
/* Usar variables de tema en CSS personalizado */
.mi-componente {
    background-color: var(--moviax-bg-primary);
    color: var(--moviax-text-primary);
    border: 1px solid var(--moviax-border);
}

.mi-boton {
    background-color: var(--moviax-primary);
    color: white;
}

.mi-boton:hover {
    background-color: var(--moviax-primary-dark);
}
```

### Variables Disponibles

#### Colores Principales
- `--moviax-primary`
- `--moviax-primary-dark`
- `--moviax-primary-light`
- `--moviax-primary-lighter`
- `--moviax-secondary`
- `--moviax-accent`

#### Fondos
- `--moviax-bg-primary`
- `--moviax-bg-secondary`
- `--moviax-bg-tertiary`
- `--moviax-bg-hover`

#### Textos
- `--moviax-text-primary`
- `--moviax-text-secondary`
- `--moviax-text-muted`
- `--moviax-text-disabled`

#### Bordes
- `--moviax-border`
- `--moviax-border-light`
- `--moviax-border-dark`

#### Sombras
- `--moviax-shadow-sm`
- `--moviax-shadow`
- `--moviax-shadow-md`
- `--moviax-shadow-lg`

#### Estados
- `--moviax-success`
- `--moviax-warning`
- `--moviax-danger`
- `--moviax-info`

---

## 🐛 Solución de Problemas

### El tema no cambia
1. Verifica que JavaScript esté habilitado en tu navegador
2. Limpia la caché del navegador
3. Verifica la consola del navegador para errores

### El tema no se guarda
1. Verifica que las cookies/localStorage estén habilitadas
2. Verifica que no estés en modo incógnito/privado
3. Limpia el localStorage: `localStorage.removeItem('moviax-theme')`

### Los colores se ven mal
1. Verifica que el archivo `moviax-theme.css` se esté cargando
2. Verifica que no haya CSS personalizado que sobrescriba los estilos
3. Prueba en otro navegador para descartar problemas de compatibilidad

### El botón no aparece
1. Verifica que el archivo `theme-switcher.js` se esté cargando
2. Verifica que Bootstrap esté cargado correctamente
3. Revisa la consola del navegador para errores

---

## 📱 Compatibilidad

### Navegadores Soportados
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ⚠️ IE11 (con limitaciones)

### Dispositivos
- ✅ Desktop (Windows, Mac, Linux)
- ✅ Tablets (iPad, Android)
- ✅ Móviles (iOS, Android)

---

## 🎓 Mejores Prácticas

### Para Usuarios
1. **Usa modo oscuro en ambientes con poca luz** para reducir fatiga visual
2. **Usa modo claro en ambientes bien iluminados** para mejor legibilidad
3. **Prueba ambos modos** para encontrar tu preferencia
4. **Usa el atajo de teclado** para cambiar rápidamente

### Para Desarrolladores
1. **Siempre usa variables CSS** en lugar de colores hardcodeados
2. **Prueba tu código en ambos temas** antes de hacer commit
3. **Verifica el contraste** de colores en modo oscuro
4. **Usa transiciones suaves** para cambios de color
5. **Respeta la preferencia del usuario** guardada en localStorage

---

## 📞 Soporte

Si tienes problemas con el theme switcher:
1. Revisa esta guía
2. Consulta la consola del navegador
3. Contacta al equipo de desarrollo
4. Reporta bugs en el sistema de tickets

---

## 📝 Changelog

### Versión 1.0.0 (13 de enero de 2026)
- ✅ Implementación inicial del theme switcher
- ✅ Modo claro y oscuro
- ✅ Persistencia en localStorage
- ✅ Detección de preferencias del sistema
- ✅ Atajo de teclado
- ✅ API JavaScript
- ✅ Eventos personalizados
- ✅ Variables CSS completas
- ✅ Transiciones suaves

---

**Desarrollado por:** Sagecores  
**Producto:** MovIAx - Sistema de Gestión Integral  
**Web:** www.sagecores.com
