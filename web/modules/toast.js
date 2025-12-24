/**
 * Toast Notification System using Notyf
 * Provides a centralized way to show success, error, warning, and info messages
 */

// Initialize Notyf with custom configuration
const notyf = new Notyf({
    duration: 4000, // 4 seconds default
    position: {
        x: 'right',
        y: 'bottom',
    },
    dismissible: true,
    ripple: true,
    types: [
        {
            type: 'success',
            background: '#10b981', // green-500
            icon: {
                className: 'notyf__icon--success',
                tagName: 'i',
            },
        },
        {
            type: 'error',
            background: '#ef4444', // red-500
            duration: 6000, // Errors stay longer
            icon: {
                className: 'notyf__icon--error',
                tagName: 'i',
            },
        },
        {
            type: 'warning',
            background: '#f59e0b', // amber-500
            icon: false,
        },
        {
            type: 'info',
            background: '#3b82f6', // blue-500
            icon: false,
        },
    ],
});

/**
 * Toast notification utility object
 */
export const toast = {
    /**
     * Show a success message
     * @param {string} message - The message to display
     * @param {number} duration - Optional duration in milliseconds
     */
    success(message, duration = 4000) {
        notyf.open({
            type: 'success',
            message,
            duration,
        });
    },

    /**
     * Show an error message
     * @param {string} message - The message to display
     * @param {number} duration - Optional duration in milliseconds
     */
    error(message, duration = 6000) {
        notyf.open({
            type: 'error',
            message,
            duration,
        });
    },

    /**
     * Show a warning message
     * @param {string} message - The message to display
     * @param {number} duration - Optional duration in milliseconds
     */
    warning(message, duration = 5000) {
        notyf.open({
            type: 'warning',
            message,
            duration,
        });
    },

    /**
     * Show an info message
     * @param {string} message - The message to display
     * @param {number} duration - Optional duration in milliseconds
     */
    info(message, duration = 4000) {
        notyf.open({
            type: 'info',
            message,
            duration,
        });
    },

    /**
     * Dismiss all toasts
     */
    dismissAll() {
        notyf.dismissAll();
    },
};

// Make toast available globally for easier access
window.toast = toast;
