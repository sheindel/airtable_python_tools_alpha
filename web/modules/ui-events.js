export function wireActions(actionHandlers = {}, changeHandlers = {}) {
    document.addEventListener("click", (event) => {
        const actionTarget = event.target.closest("[data-action]");
        if (!actionTarget) return;

        const handler = actionHandlers[actionTarget.dataset.action];
        if (handler) {
            handler(event, actionTarget);
        }
    });

    document.addEventListener("change", (event) => {
        const changeTarget = event.target.closest("[data-change-action]");
        if (!changeTarget) return;

        const handler = changeHandlers[changeTarget.dataset.changeAction];
        if (handler) {
            handler(event, changeTarget);
        }
    });
}
