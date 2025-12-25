/**
 * Control de Gastos - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    initTooltips();
    
    // Initialize password toggles
    initPasswordToggles();
    
    // Initialize loading buttons
    initLoadingButtons();
    
    // Initialize keyboard shortcuts
    initKeyboardShortcuts();
    
    // Initialize toasts from session messages
    initSessionToasts();
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
    
    if (!toastEl) return;
    
    // Set icon based on type
    const icons = {
        success: 'bi-check-circle-fill',
        danger: 'bi-x-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info: 'bi-info-circle-fill'
    };
    
    // Reset classes
    toastEl.className = 'toast align-items-center border-0';
    toastEl.classList.add(`bg-${type}`, 'text-white');
    
    // Set content
    toastIcon.className = `bi ${icons[type] || icons.info} me-2`;
    toastMessage.textContent = message;
    
    // Show toast
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
}

// Make showToast globally available
window.showToast = showToast;

