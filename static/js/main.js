/**
 * Control de Gastos - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips first so sidebar toggle can enable/disable them
    initTooltips();

    // Initialize sidebar toggle (reads localStorage and sets initial state)
    initSidebarToggle();

    // Close mobile offcanvas when a nav link is clicked
    initMobileOffcanvas();

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

    // Show "Nuevo" badge on whats-new link if unseen version
    initWhatsNewBadge();

    // Collapsible category groups (categories list page)
    initCategoryCollapse();

    // Drag & drop reorder for category groups
    initCategoryReorder();

    // Expense subcategory filter (expense list page)
    initExpenseSubcategoryFilter();

    // Mark whats-new page as seen
    initWhatsNewSeen();

    // Feedback form validation
    initFeedbackForm();

    // FAB contextual by section
    initFab();

    // Back button
    initBackButton();

    // Landing: fallback CSP-safe para imágenes de showcase
    initShowcaseImageFallback();

    // Dark mode toggle
    initDarkMode();
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
                const originalContent = submitBtn.innerHTML;
                submitBtn.dataset.originalContent = originalContent;

                // Defer so other submit listeners (validation) run first
                setTimeout(() => {
                    if (e.defaultPrevented) return;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = `
                        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Procesando...
                    `;
                    // Fallback re-enable
                    setTimeout(() => {
                        if (submitBtn.disabled) {
                            submitBtn.disabled = false;
                            submitBtn.innerHTML = originalContent;
                        }
                    }, 10000);
                }, 0);
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
            const appData = document.getElementById('app-data');
            window.location.href = appData ? appData.dataset.dashboardUrl : '/dashboard/';
        }
    });
}

/**
 * Initialize toasts from session messages
 */
function initSessionToasts() {
    const appData = document.getElementById('app-data');
    if (!appData) return;
    const raw = appData.dataset.messages;
    if (!raw) return;

    raw.split(';;').forEach((entry, i) => {
        const parts = entry.split('||');
        const message = parts[0] || '';
        const tags = parts[1] || '';
        if (!message) return;
        let type = 'info';
        if (tags.includes('success')) type = 'success';
        else if (tags.includes('error')) type = 'danger';
        else if (tags.includes('warning')) type = 'warning';
        setTimeout(() => showToast(message, type), 150 + i * 300);
    });

    // Clear so re-renders don't re-show (remove the attribute)
    appData.removeAttribute('data-messages');
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
    const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 5000 });
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
 * Close mobile offcanvas when a nav link is clicked inside it.
 * Also ensures the offcanvas is properly hidden when the viewport
 * crosses the md breakpoint (e.g., device rotation).
 */
function initMobileOffcanvas() {
    const offcanvasEl = document.getElementById('mobileSidebar');
    if (!offcanvasEl) return;

    // Close offcanvas on any nav link click (so navigating works cleanly)
    offcanvasEl.querySelectorAll('a.nav-link').forEach(link => {
        link.addEventListener('click', function() {
            const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
            if (bsOffcanvas) bsOffcanvas.hide();
        });
    });

    // When viewport goes above md breakpoint, hide the offcanvas if open
    const mdBreakpoint = window.matchMedia('(min-width: 768px)');
    mdBreakpoint.addEventListener('change', function(e) {
        if (e.matches) {
            const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl);
            if (bsOffcanvas) bsOffcanvas.hide();
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
 * Muestra badge "Nuevo" en el link de Novedades si hay versión no vista
 */
function initWhatsNewBadge() {
    const appData = document.getElementById('app-data');
    const currentVersion = appData ? appData.dataset.appVersion : '';
    const seen = localStorage.getItem('whats_new_seen');
    if (currentVersion && seen !== currentVersion) {
        document.querySelectorAll('#sidebarNewBadge').forEach(el => {
            el.style.display = 'inline';
        });
    }
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

/**
 * Mark the whats-new page as seen so the sidebar badge disappears.
 * Only runs when #whats-new-marker is present (whats_new page).
 */
function initWhatsNewSeen() {
    const marker = document.getElementById('whats-new-marker');
    if (!marker) return;
    const version = marker.dataset.version;
    if (version) localStorage.setItem('whats_new_seen', version);
}

/**
 * Feedback form: clear error on input, prevent submit when empty,
 * show loading state on valid submit.
 * Only runs when #feedbackSubmitBtn is present (feedback page).
 */
function initFeedbackForm() {
    const submitBtn = document.getElementById('feedbackSubmitBtn');
    if (!submitBtn) return;

    const form = submitBtn.closest('form');
    const errorDiv = document.getElementById('mensajeError');
    // Find the textarea inside the form
    const textarea = form ? form.querySelector('textarea') : null;

    if (textarea && errorDiv) {
        textarea.addEventListener('input', function () {
            if (this.value.trim().length > 0) {
                errorDiv.style.display = 'none';
            }
        });
    }

    if (form && submitBtn) {
        form.addEventListener('submit', function (e) {
            if (!textarea || textarea.value.trim().length === 0) {
                e.preventDefault();
                if (errorDiv) errorDiv.style.display = 'block';
                if (textarea) textarea.focus();
                return;
            }
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span>Procesando...';
        });
    }
}

/**
 * Expense list: filter subcategory options based on selected group.
 * Only runs on the expense list page (no-op elsewhere).
 */
function initExpenseSubcategoryFilter() {
    const groupSelect = document.getElementById('id_category');
    const subSelect = document.getElementById('id_subcategory');
    const subWrapper = document.getElementById('subcategory-wrapper');
    if (!groupSelect || !subSelect || !subWrapper) return;

    const allOptions = Array.from(subSelect.querySelectorAll('option[data-parent]'));

    function filterSubs(parentId) {
        const currentVal = subSelect.value;
        allOptions.forEach(opt => { opt.hidden = true; opt.disabled = true; });

        if (!parentId) {
            subWrapper.style.display = 'none';
            subSelect.value = '';
            return;
        }
        subWrapper.style.display = '';
        let hasVisible = false;
        allOptions.forEach(opt => {
            if (String(opt.dataset.parent) === String(parentId)) {
                opt.hidden = false;
                opt.disabled = false;
                hasVisible = true;
            }
        });
        if (currentVal && subSelect.querySelector(`option[value="${currentVal}"]:not([hidden])`)) {
            subSelect.value = currentVal;
        } else {
            subSelect.value = '';
        }
        if (!hasVisible) subWrapper.style.display = 'none';
    }

    groupSelect.addEventListener('change', () => filterSubs(groupSelect.value));
    filterSubs(groupSelect.value);
}

/**
 * Collapsible category groups with localStorage persistence.
 * Only runs on the categories list page (no-op elsewhere).
 */
function initCategoryCollapse() {
    const STORAGE_KEY = 'category_collapsed_groups';

    function loadState() {
        try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; } catch (e) { return {}; }
    }
    function saveState(state) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }

    const toggleBtns = document.querySelectorAll(
        '[data-bs-toggle="collapse"][data-bs-target^="#expense-group-"], ' +
        '[data-bs-toggle="collapse"][data-bs-target^="#income-group-"]'
    );
    if (!toggleBtns.length) return;

    const state = loadState();

    toggleBtns.forEach(btn => {
        const targetId = btn.getAttribute('data-bs-target').replace('#', '');
        const collapseEl = document.getElementById(targetId);
        if (!collapseEl) return;

        const chevron = btn.querySelector('.category-chevron');

        // Restore saved state (false = collapsed)
        if (state[targetId] === false) {
            collapseEl.classList.remove('show');
            btn.setAttribute('aria-expanded', 'false');
            if (chevron) chevron.style.transform = 'rotate(-90deg)';
        }

        collapseEl.addEventListener('hide.bs.collapse', () => {
            state[targetId] = false;
            saveState(state);
            if (chevron) chevron.style.transform = 'rotate(-90deg)';
        });
        collapseEl.addEventListener('show.bs.collapse', () => {
            state[targetId] = true;
            saveState(state);
            if (chevron) chevron.style.transform = '';
        });
    });
}

/**
 * Drag & drop reorder for category groups using SortableJS.
 * Only runs on the categories list page (no-op elsewhere).
 */
function initCategoryReorder() {
    if (typeof Sortable === 'undefined') return;

    ['expense-sortable', 'income-sortable'].forEach(containerId => {
        const container = document.getElementById(containerId);
        if (!container) return;
        const reorderUrl = container.dataset.reorderUrl;
        if (!reorderUrl) return;

        Sortable.create(container, {
            handle: '.sortable-handle',
            animation: 150,
            onEnd: function() {
                const ids = Array.from(container.querySelectorAll('[data-group-id]'))
                    .map(el => parseInt(el.dataset.groupId, 10));

                fetch(reorderUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({ ids }),
                }).then(res => {
                    if (!res.ok) showToast('No se pudo guardar el orden.', 'danger');
                }).catch(() => showToast('Error al guardar el orden.', 'danger'));
            },
        });
    });
}

function getCsrfToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el) return el.value;
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.trim().split('=')[1] : '';
}

function initBackButton() {
    const btn = document.getElementById('back-btn');
    if (!btn) return;
    const ref = document.referrer;
    if (ref && new URL(ref).hostname === window.location.hostname) {
        btn.classList.remove('d-none');
        btn.addEventListener('click', function () {
            history.back();
        });
    }
}

function initFab() {
    const fab = document.querySelector('.fab-button');
    if (!fab) return;

    const appData = document.getElementById('app-data');
    if (!appData) return;

    const path = window.location.pathname;
    let url = appData.dataset.expenseCreateUrl;
    let label = 'Nuevo Gasto (Ctrl+N)';

    if (path.startsWith('/income/')) {
        url = appData.dataset.incomeCreateUrl;
        label = 'Nuevo Ingreso (Ctrl+N)';
    } else if (path.startsWith('/savings/')) {
        url = appData.dataset.savingCreateUrl;
        label = 'Nueva Meta de Ahorro (Ctrl+N)';
    } else if (path.startsWith('/recurring/')) {
        url = appData.dataset.recurringCreateUrl;
        label = 'Nuevo Gasto Fijo (Ctrl+N)';
    } else if (path.startsWith('/categories/')) {
        url = appData.dataset.categoryCreateUrl;
        label = 'Nueva Categoría (Ctrl+N)';
    }

    fab.href = url;
    fab.setAttribute('aria-label', label);

    // Update Bootstrap tooltip instance if already initialized
    const tooltipInstance = bootstrap.Tooltip.getInstance(fab);
    if (tooltipInstance) {
        tooltipInstance.dispose();
    }
    fab.title = label;
    new bootstrap.Tooltip(fab);
}


function initShowcaseImageFallback() {
    document.querySelectorAll('.showcase-img-wrapper img').forEach(function(img) {
        img.addEventListener('error', function() {
            this.style.display = 'none';
            const placeholder = this.nextElementSibling;
            if (placeholder) placeholder.style.display = 'flex';
        });
    });
}

function initDarkMode() {
    const toggle = document.getElementById('darkModeToggle');
    if (!toggle) return;

    const icon = document.getElementById('darkModeIcon');
    const label = document.getElementById('darkModeLabel');
    const html = document.documentElement;

    function applyTheme(dark) {
        html.setAttribute('data-bs-theme', dark ? 'dark' : 'light');
        if (icon) {
            icon.className = dark ? 'bi bi-sun me-2' : 'bi bi-moon me-2';
        }
        if (label) {
            label.textContent = dark ? 'Modo claro' : 'Modo oscuro';
        }
    }

    const isDark = localStorage.getItem('theme') === 'dark';
    applyTheme(isDark);

    toggle.addEventListener('click', function() {
        const nowDark = html.getAttribute('data-bs-theme') !== 'dark';
        localStorage.setItem('theme', nowDark ? 'dark' : 'light');
        applyTheme(nowDark);
    });
}
