/**
 * DARKSULFOCUS - Main Application JavaScript
 * Handles sidebar navigation, notifications, and general UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
    initializeNotifications();
    initializeFormValidation();
    initializeTooltips();
});

/**
 * Sidebar Navigation Management
 */
function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mainContent = document.getElementById('mainContent');

    if (!sidebarToggle || !sidebar || !sidebarOverlay) return;

    // Toggle sidebar
    sidebarToggle.addEventListener('click', function() {
        toggleSidebar();
    });

    // Close sidebar when clicking overlay
    sidebarOverlay.addEventListener('click', function() {
        closeSidebar();
    });

    // Close sidebar when clicking outside (anywhere in main content)
    document.addEventListener('click', function(e) {
        if (sidebar.classList.contains('active') && 
            !sidebar.contains(e.target) && 
            !sidebarToggle.contains(e.target)) {
            closeSidebar();
        }
    });

    // Close sidebar on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (sidebar.classList.contains('active')) {
        closeSidebar();
    } else {
        openSidebar();
    }
}

function openSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    sidebar.style.display = 'block'; // Show sidebar first
    setTimeout(() => {
        sidebar.classList.add('active');
        sidebarOverlay.classList.add('active');
    }, 10); // Small delay for smooth animation
    document.body.style.overflow = 'hidden';
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    sidebar.classList.remove('active');
    sidebarOverlay.classList.remove('active');
    document.body.style.overflow = '';
    
    // Hide sidebar after animation completes
    setTimeout(() => {
        if (!sidebar.classList.contains('active')) {
            sidebar.style.display = 'none';
        }
    }, 300); // Match transition duration
}

/**
 * Notification Management
 */
function initializeNotifications() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // Request notification permission for timer alerts
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

/**
 * Show browser notification
 */
function showNotification(title, message, icon = '/static/favicon.ico') {
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: message,
            icon: icon,
            badge: icon,
            tag: 'darksulfocus-timer'
        });

        // Auto close after 5 seconds
        setTimeout(() => notification.close(), 5000);

        return notification;
    }
}

/**
 * Show success toast
 */
function showSuccessToast(message) {
    showToast(message, 'success');
}

/**
 * Show error toast
 */
function showErrorToast(message) {
    showToast(message, 'danger');
}

/**
 * Show info toast
 */
function showInfoToast(message) {
    showToast(message, 'info');
}

/**
 * Generic toast function
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);

    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 4000
    });
    toast.show();

    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * Form Validation Enhancement
 */
function initializeFormValidation() {
    // Add real-time validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                showErrorToast('Please fill in all required fields correctly.');
            }
            form.classList.add('was-validated');
        });

        // Real-time validation for inputs
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateField(input);
            });

            input.addEventListener('input', function() {
                if (input.classList.contains('is-invalid')) {
                    validateField(input);
                }
            });
        });
    });
}

function validateField(field) {
    const isValid = field.checkValidity();
    
    field.classList.remove('is-valid', 'is-invalid');
    
    if (field.value.trim() !== '') {
        if (isValid) {
            field.classList.add('is-valid');
        } else {
            field.classList.add('is-invalid');
        }
    }
}

/**
 * Initialize Bootstrap Tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Utility Functions
 */
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatDuration(minutes) {
    if (minutes < 60) {
        return `${minutes}m`;
    } else {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    }
}

/**
 * Confirmation Dialogs
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Loading States
 */
function showLoading(element, text = 'Loading...') {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        element.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                ${text}
            </div>
        `;
        element.disabled = true;
    }
}

function hideLoading(element, originalText) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

/**
 * Local Storage Utilities
 */
function saveToLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.warn('LocalStorage not available:', e);
    }
}

function getFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
        console.warn('Error reading from LocalStorage:', e);
        return defaultValue;
    }
}

function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (e) {
        console.warn('Error removing from LocalStorage:', e);
    }
}

/**
 * Theme Management (if needed for future enhancements)
 */
function initializeTheme() {
    const savedTheme = getFromLocalStorage('theme', 'dark');
    document.documentElement.setAttribute('data-theme', savedTheme);
}

/**
 * Export functions for global access
 */
window.DarkSulFocus = {
    toggleSidebar,
    openSidebar,
    closeSidebar,
    showNotification,
    showSuccessToast,
    showErrorToast,
    showInfoToast,
    formatTime,
    formatDuration,
    confirmAction,
    showLoading,
    hideLoading,
    saveToLocalStorage,
    getFromLocalStorage,
    removeFromLocalStorage
};
