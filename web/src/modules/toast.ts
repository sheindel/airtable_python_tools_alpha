/**
 * Toast Notification System using Notyf
 * Provides a centralized way to show success, error, warning, and info messages
 */

// Type definitions for Notyf (external library)
interface NotyfOptions {
    duration?: number;
    position?: {
        x: 'left' | 'center' | 'right';
        y: 'top' | 'center' | 'bottom';
    };
    dismissible?: boolean;
    ripple?: boolean;
    types?: NotyfTypeOptions[];
}

interface NotyfTypeOptions {
    type: string;
    background?: string;
    duration?: number;
    icon?: {
        className: string;
        tagName: string;
    } | false;
}

interface NotyfOpenOptions {
    type: string;
    message: string;
    duration?: number;
}

interface NotyfInstance {
    open(options: NotyfOpenOptions): void;
    dismissAll(): void;
}

// Declare Notyf constructor from global scope
declare const Notyf: new (options: NotyfOptions) => NotyfInstance;

// Initialize Notyf with custom configuration
const notyf: NotyfInstance = new Notyf({
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
export interface Toast {
    success(message: string, duration?: number): void;
    error(message: string, duration?: number): void;
    warning(message: string, duration?: number): void;
    info(message: string, duration?: number): void;
    dismissAll(): void;
}

export const toast: Toast = {
    /**
     * Show a success message
     * @param message - The message to display
     * @param duration - Optional duration in milliseconds
     */
    success(message: string, duration: number = 4000): void {
        notyf.open({
            type: 'success',
            message,
            duration,
        });
    },

    /**
     * Show an error message
     * @param message - The message to display
     * @param duration - Optional duration in milliseconds
     */
    error(message: string, duration: number = 6000): void {
        notyf.open({
            type: 'error',
            message,
            duration,
        });
    },

    /**
     * Show a warning message
     * @param message - The message to display
     * @param duration - Optional duration in milliseconds
     */
    warning(message: string, duration: number = 5000): void {
        notyf.open({
            type: 'warning',
            message,
            duration,
        });
    },

    /**
     * Show an info message
     * @param message - The message to display
     * @param duration - Optional duration in milliseconds
     */
    info(message: string, duration: number = 4000): void {
        notyf.open({
            type: 'info',
            message,
            duration,
        });
    },

    /**
     * Dismiss all toasts
     */
    dismissAll(): void {
        notyf.dismissAll();
    },
};

// Extend window interface to include toast
declare global {
    interface Window {
        toast: Toast;
    }
}

// Make toast available globally for easier access
window.toast = toast;
