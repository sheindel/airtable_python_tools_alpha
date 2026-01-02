/**
 * UI Events Module
 * Handles event delegation for action buttons and change events.
 * Provides a centralized event handling system for the entire application.
 */

type ActionHandler = (event?: Event, target?: HTMLElement) => void;

/**
 * Wire up action and change handlers to the document
 * @param actionHandlers - Map of data-action values to handler functions
 * @param changeHandlers - Map of data-change-action values to handler functions
 */
export function wireActions(
    actionHandlers: Record<string, ActionHandler> = {},
    changeHandlers: Record<string, ActionHandler> = {}
): void {
    // Handle click events with data-action attribute
    document.addEventListener("click", (event) => {
        const actionTarget = (event.target as HTMLElement).closest("[data-action]") as HTMLElement | null;
        if (!actionTarget) return;

        const actionName = actionTarget.dataset.action;
        if (actionName) {
            const handler = actionHandlers[actionName];
            if (handler) {
                handler(event, actionTarget);
            }
        }
    });

    // Handle change events with data-change-action attribute
    document.addEventListener("change", (event) => {
        const changeTarget = (event.target as HTMLElement).closest("[data-change-action]") as HTMLElement | null;
        if (!changeTarget) return;

        const changeAction = changeTarget.dataset.changeAction;
        if (changeAction) {
            const handler = changeHandlers[changeAction];
            if (handler) {
                handler(event, changeTarget);
            }
        }
    });
}
