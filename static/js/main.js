/**
 * Control de Gastos - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips first so sidebar toggle can enable/disable them
    initTooltips();

    // Initialize sidebar toggle (reads localStorage and sets initial state)
    initSidebarToggle();

    // Initialize password toggles
    initPasswordToggles();

    // Initialize loading buttons
    initLoadingButtons();

    // Initialize keyboard shortcuts
    initKeyboardShortcuts();

    // Initialize toasts from session messages
    initSessionToasts();

    // Initialize transaction forms
    initTransactionForms();

    // Initialize quick deposit modal
    initQuickDepositModal();

    // Apply dynamic colors
    initDynamicColors();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
}

/**
 * Password visibility toggle (QW-1.2)
 */
function initPasswordToggles() {
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.closest('.input-group').querySelector('input');
            const icon = this.querySelector('i');

            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    });
}

/**
 * Loading state for form buttons (QW-1.1)
 */
function initLoadingButtons() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                // Store original content
                const originalContent = submitBtn.innerHTML;
                submitBtn.dataset.originalContent = originalContent;

                // Show loading state
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Procesando...
                `;

                // Re-enable after timeout (fallback)
                setTimeout(() => {
                    if (submitBtn.disabled) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalContent;
                    }
                }, 10000);
            }
        });
    });
}

/**
 * Keyboard shortcuts for power users (M-2.2)
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only if not in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        // Ctrl+N = New expense
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            const fabButton = document.querySelector('.fab-button');
            if (fabButton) {
                window.location.href = fabButton.href;
            }
        }

        // Ctrl+D = Dashboard
        if (e.ctrlKey && e.key === 'd') {
            e.preventDefault();
            window.location.href = '/';
        }
    });
}

/**
 * Initialize toasts from session messages
 */
function initSessionToasts() {
    // Check for Django messages in the page
    const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Show toast notification (QW-3.3)
 * @param {string} message - Message to display
 * @param {string} type - Type: success, danger, warning, info
 */
function showToast(message, type = 'success') {
    const toastEl = document.getElementById('actionToast');
    const toastIcon = document.getElementById('toastIcon');
    const toastMessage = document.getElementById('toastMessage');
    const toastCloseBtn = document.getElementById('toastCloseBtn');

    if (!toastEl) return;

    const icons = {
        success: 'bi-check-circle-fill',
        danger: 'bi-x-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info: 'bi-info-circle-fill'
    };

    // Reset classes base
    toastEl.className = 'toast align-items-center border-0';

    // Background
    toastEl.classList.add(`bg-${type}`);

    // Text color: warning/info son fondos claros -> texto oscuro
    const isLightBg = ['warning', 'info'].includes(type);
    toastEl.classList.add(isLightBg ? 'text-dark' : 'text-white');

    // Close button contrast
    if (toastCloseBtn) {
        toastCloseBtn.classList.remove('btn-close-white');
        const needsWhiteClose = !isLightBg; // success/danger -> blanco
        if (needsWhiteClose) toastCloseBtn.classList.add('btn-close-white');
    }

    // Content
    toastIcon.className = `bi ${icons[type] || icons.info} me-2`;
    toastMessage.textContent = message;

    // Show
    const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 4000 });
    toast.show();
}

// Make showToast globally available
window.showToast = showToast;

/**
 * Initialize transaction forms by detecting form ID in DOM
 */
function initTransactionForms() {
    if (document.getElementById('expenseForm')) {
        initTransactionForm('expenseForm');
    }
    if (document.getElementById('incomeForm')) {
        initTransactionForm('incomeForm');
    }
}

/**
 * Initialize quick deposit modal
 */
function initQuickDepositModal() {
    const modal = document.getElementById('quickDepositModal');
    if (!modal) return;
    modal.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        const url = button.getAttribute('data-url');
        const name = button.getAttribute('data-name');
        const current = parseFloat(button.getAttribute('data-current') || 0);
        const target = parseFloat(button.getAttribute('data-target') || 0);
        const progress = parseFloat(button.getAttribute('data-progress') || 0);

        document.getElementById('quickDepositForm').action = url;
        document.getElementById('quickDepositSavingName').textContent = name;

        const currentEl = document.getElementById('quickDepositCurrent');
        const progressEl = document.getElementById('quickDepositProgress');
        const barEl = document.getElementById('quickDepositProgressBar');

        if (currentEl) currentEl.textContent = `$ ${current.toLocaleString('es-AR', {minimumFractionDigits: 2})} / $ ${target.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
        if (progressEl) progressEl.textContent = `${progress}%`;
        if (barEl) {
            barEl.style.width = Math.min(progress, 100) + '%';
            barEl.style.visibility = 'visible';
        }
    });
}

/**
 * Collapsible sidebar with localStorage persistence
 */
function initSidebarToggle() {
    const sidebar = document.getElementById('appSidebar');
    const mainContent = document.getElementById('appMain');
    const toggleBtn = document.getElementById('sidebarToggle');
    const toggleIcon = document.getElementById('sidebarToggleIcon');
    const toggleText = document.getElementById('sidebarToggleText');

    if (!sidebar || !toggleBtn) return;

    const STORAGE_KEY = 'sidebar_collapsed';

    function setCollapsed(collapsed) {
        sidebar.classList.toggle('sidebar--collapsed', collapsed);
        if (mainContent) mainContent.classList.toggle('app-main--sidebar-collapsed', collapsed);
        toggleIcon.className = collapsed ? 'bi bi-layout-sidebar' : 'bi bi-layout-sidebar-reverse';
        if (toggleText) toggleText.textContent = collapsed ? 'Expandir' : 'Contraer';
    }

    const savedState = localStorage.getItem(STORAGE_KEY) === 'true';
    setCollapsed(savedState);

    toggleBtn.addEventListener('click', function() {
        const next = !sidebar.classList.contains('sidebar--collapsed');
        setCollapsed(next);
        localStorage.setItem(STORAGE_KEY, String(next));
    });
}

/**
 * Apply dynamic colors from data-color attributes (anti-FOUC)
 */
function initDynamicColors() {
    // Simple color: data-color + optional data-color-prop
    document.querySelectorAll('[data-color]').forEach(el => {
        const color = el.getAttribute('data-color');
        const prop = el.getAttribute('data-color-prop') || 'color';
        if (color) el.style[prop] = color;
        el.style.visibility = 'visible';
    });

    // Color with hex opacity suffix: data-color-bg + data-color-opacity
    document.querySelectorAll('[data-color-bg]').forEach(el => {
        const color = el.getAttribute('data-color-bg');
        const suffix = el.getAttribute('data-color-opacity') || '';
        if (color) el.style.backgroundColor = color + suffix;
        el.style.visibility = 'visible';
    });

    // Progress bar width: data-width
    document.querySelectorAll('[data-width]').forEach(el => {
        const width = el.getAttribute('data-width');
        if (width) el.style.width = width + '%';
        el.style.visibility = 'visible';
    });

    // Progress bar width + color combined
    document.querySelectorAll('[data-progress-color]').forEach(el => {
        const color = el.getAttribute('data-progress-color');
        if (color) el.style.backgroundColor = color;
        el.style.visibility = 'visible';
    });
}
