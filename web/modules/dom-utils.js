export function getDropdown(id) {
    return document.getElementById(id);
}

export function setDropdownOptions(id, options) {
    const dropdown = getDropdown(id);
    if (dropdown && dropdown.tagName === "AT-DROPDOWN") {
        dropdown.options = options;
    }
}

export function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

export function copyToClipboard(elementId, description = "Content", event) {
    const element = document.getElementById(elementId);
    const text = element?.textContent || "";

    if (!text || text.includes("No formula selected") || text.includes("Select a formula field")) {
        alert(`No ${description.toLowerCase()} to copy`);
        return;
    }

    navigator.clipboard.writeText(text).then(() => {
        if (event && event.currentTarget) {
            const button = event.currentTarget;
            const originalHTML = button.innerHTML;
            button.innerHTML = '<svg class="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
            button.style.opacity = "100";
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.style.opacity = "";
            }, 1500);
        }
    }).catch((error) => {
        console.error("Error copying to clipboard:", error);
        alert(`Failed to copy ${description.toLowerCase()} to clipboard`);
    });
}
