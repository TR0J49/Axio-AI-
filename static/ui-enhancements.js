/**
 * AXIO AI - UI Enhancements
 * Modern UI interactions and animations
 * by Perfionix AI
 */

// ================================
// TOAST NOTIFICATIONS
// ================================

class ToastManager {
    constructor() {
        this.container = document.getElementById('toast-container');
        this.toasts = [];
    }

    show(message, type = 'info', duration = 3000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);
        this.toasts.push(toast);

        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);

        // Auto remove
        if (duration > 0) {
            setTimeout(() => this.remove(toast), duration);
        }

        return toast;
    }

    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = this.getIcon(type);

        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content">
                <div class="toast-title">${this.getTitle(type)}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="toastManager.remove(this.parentElement)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;

        return toast;
    }

    getIcon(type) {
        const icons = {
            success: `<svg viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>`,
            error: `<svg viewBox="0 0 24 24" fill="none" stroke="#f5576c" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>`,
            info: `<svg viewBox="0 0 24 24" fill="none" stroke="#667eea" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>`,
            warning: `<svg viewBox="0 0 24 24" fill="none" stroke="#fee140" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>`
        };
        return icons[type] || icons.info;
    }

    getTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            info: 'Info',
            warning: 'Warning'
        };
        return titles[type] || 'Notification';
    }

    remove(toast) {
        toast.classList.add('removing');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
            const index = this.toasts.indexOf(toast);
            if (index > -1) {
                this.toasts.splice(index, 1);
            }
        }, 300);
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }
}

// Initialize toast manager
const toastManager = new ToastManager();

// ================================
// LOADING STATES
// ================================

class LoadingManager {
    static show(element, text = 'Loading...') {
        if (!element) return;

        element.classList.add('loading');
        element.setAttribute('data-original-content', element.innerHTML);

        element.innerHTML = `
            <div class="loading-spinner">
                <div class="progress-circular"></div>
                <span>${text}</span>
            </div>
        `;
        element.disabled = true;
    }

    static hide(element) {
        if (!element) return;

        const originalContent = element.getAttribute('data-original-content');
        if (originalContent) {
            element.innerHTML = originalContent;
            element.removeAttribute('data-original-content');
        }
        element.classList.remove('loading');
        element.disabled = false;
    }
}

// ================================
// RIPPLE EFFECT
// ================================

function addRippleEffect() {
    document.querySelectorAll('.btn-primary, .btn-icon, .nav-item').forEach(button => {
        if (!button.classList.contains('ripple')) {
            button.classList.add('ripple');
        }
    });
}

// ================================
// SMOOTH SCROLL
// ================================

function smoothScrollTo(element, duration = 500) {
    const target = typeof element === 'string' ? document.querySelector(element) : element;
    if (!target) return;

    const targetPosition = target.offsetTop;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;

    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = ease(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }

    function ease(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }

    requestAnimationFrame(animation);
}

// ================================
// PARTICLE EFFECTS
// ================================

class ParticleEffect {
    constructor(container, count = 20) {
        this.container = container;
        this.count = count;
        this.particles = [];
    }

    create() {
        const particlesContainer = document.createElement('div');
        particlesContainer.className = 'particles';
        this.container.appendChild(particlesContainer);

        for (let i = 0; i < this.count; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 3 + 's';
            particle.style.animationDuration = (Math.random() * 2 + 2) + 's';
            particlesContainer.appendChild(particle);
            this.particles.push(particle);
        }
    }

    destroy() {
        const particlesContainer = this.container.querySelector('.particles');
        if (particlesContainer) {
            particlesContainer.remove();
        }
        this.particles = [];
    }
}

// ================================
// ENHANCED ANIMATIONS
// ================================

// Intersection Observer for scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

function observeElements() {
    document.querySelectorAll('.message, .task-item, .note-card, .kpi-card').forEach(el => {
        observer.observe(el);
    });
}

// ================================
// COPY TO CLIPBOARD
// ================================

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        toastManager.success('Copied to clipboard!', 2000);
        return true;
    } catch (err) {
        toastManager.error('Failed to copy', 2000);
        return false;
    }
}

// ================================
// KEYBOARD SHORTCUTS
// ================================

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => {
            const key = this.getKeyString(e);
            const handler = this.shortcuts.get(key);
            if (handler) {
                e.preventDefault();
                handler(e);
            }
        });
    }

    getKeyString(e) {
        const parts = [];
        if (e.ctrlKey) parts.push('Ctrl');
        if (e.altKey) parts.push('Alt');
        if (e.shiftKey) parts.push('Shift');
        if (e.metaKey) parts.push('Meta');
        parts.push(e.key);
        return parts.join('+');
    }

    register(keyCombo, handler) {
        this.shortcuts.set(keyCombo, handler);
    }

    unregister(keyCombo) {
        this.shortcuts.delete(keyCombo);
    }
}

const shortcuts = new KeyboardShortcuts();

// Register common shortcuts
shortcuts.register('Ctrl+/', () => {
    document.getElementById('chat-input')?.focus();
});

shortcuts.register('Escape', () => {
    const modal = document.getElementById('modal');
    if (modal && modal.style.display !== 'none') {
        modal.style.display = 'none';
    }
});

// ================================
// THEME UTILITIES
// ================================

class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.apply();
    }

    apply() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
    }

    toggle() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', this.currentTheme);
        this.apply();
        toastManager.info(`Switched to ${this.currentTheme} theme`, 2000);
    }
}

const themeManager = new ThemeManager();

// ================================
// PERFORMANCE UTILITIES
// ================================

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ================================
// INITIALIZATION
// ================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🎨 UI Enhancements loaded');

    // Add ripple effects
    addRippleEffect();

    // Observe elements for scroll animations
    observeElements();

    // Re-observe when new elements are added
    const mutationObserver = new MutationObserver(debounce(() => {
        addRippleEffect();
        observeElements();
    }, 100));

    mutationObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// ================================
// EXPORT FOR GLOBAL USE
// ================================

window.UIEnhancements = {
    toast: toastManager,
    loading: LoadingManager,
    particles: ParticleEffect,
    copyToClipboard,
    smoothScrollTo,
    shortcuts,
    theme: themeManager,
    debounce,
    throttle
};

console.log('✨ Axio UI Enhancements initialized');
