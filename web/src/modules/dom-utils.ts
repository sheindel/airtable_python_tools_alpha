import type { AtDropdownElement } from '../types/dom';
import type { DropdownOption } from '../types/pyscript';
import { toast } from './toast.js';

/**
 * Get a dropdown element by ID
 * @param id - The element ID
 * @returns The dropdown element or null if not found or not a dropdown
 */
export function getDropdown(id: string): AtDropdownElement | null {
    const element = document.getElementById(id);
    if (element && element.tagName === "AT-DROPDOWN") {
        return element as AtDropdownElement;
    }
    return null;
}

/**
 * Set options for a dropdown element
 * @param id - The dropdown element ID
 * @param options - Array of dropdown options
 */
export function setDropdownOptions(id: string, options: DropdownOption[]): void {
    const dropdown = getDropdown(id);
    if (dropdown) {
        dropdown.options = options;
    }
}

/**
 * Escape HTML special characters in text
 * @param text - The text to escape
 * @returns HTML-escaped text
 */
export function escapeHtml(text: string): string {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Copy text content from an element to clipboard with visual feedback
 * @param elementId - The ID of the element containing text to copy
 * @param description - Description of the content being copied (for user feedback)
 * @param event - Optional mouse event to show visual feedback on the button
 */
export function copyToClipboard(
    elementId: string,
    description: string = "Content",
    event?: MouseEvent
): void {
    const element = document.getElementById(elementId);
    const text = element?.textContent || "";

    if (!text || text.includes("No formula selected") || text.includes("Select a formula field")) {
        toast.warning(`No ${description.toLowerCase()} to copy`);
        return;
    }

    navigator.clipboard.writeText(text).then(() => {
        if (event && event.currentTarget) {
            const button = event.currentTarget as HTMLElement;
            const originalHTML = button.innerHTML;
            button.innerHTML = '<svg class="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
            button.style.opacity = "100";
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.style.opacity = "";
            }, 1500);
        }
    }).catch((error: Error) => {
        console.error("Error copying to clipboard:", error);
        toast.error(`Failed to copy ${description.toLowerCase()} to clipboard`);
    });
}

/**
 * Format a timestamp as a relative time string (e.g., "5 minutes ago", "3 hours ago")
 * @param timestamp - ISO 8601 timestamp string
 * @returns Relative time string
 */
export function formatRelativeTime(timestamp: string): string {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    const diffWeek = Math.floor(diffDay / 7);
    const diffMonth = Math.floor(diffDay / 30);
    const diffYear = Math.floor(diffDay / 365);

    if (diffSec < 10) {
        return "just now";
    } else if (diffSec < 60) {
        return `${diffSec} seconds ago`;
    } else if (diffMin === 1) {
        return "1 minute ago";
    } else if (diffMin < 60) {
        return `${diffMin} minutes ago`;
    } else if (diffHour === 1) {
        return "1 hour ago";
    } else if (diffHour < 24) {
        return `${diffHour} hours ago`;
    } else if (diffDay === 1) {
        return "1 day ago";
    } else if (diffDay < 7) {
        return `${diffDay} days ago`;
    } else if (diffWeek === 1) {
        return "1 week ago";
    } else if (diffWeek < 4) {
        return `${diffWeek} weeks ago`;
    } else if (diffMonth === 1) {
        return "1 month ago";
    } else if (diffMonth < 12) {
        return `${diffMonth} months ago`;
    } else if (diffYear === 1) {
        return "1 year ago";
    } else {
        return `${diffYear} years ago`;
    }
}
