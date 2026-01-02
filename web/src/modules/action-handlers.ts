/**
 * Action Handlers Module
 * Central registry for all action handlers and event listeners.
 * Provides a unified interface for button clicks, change events, and modal interactions.
 */

import { copyToClipboard } from "./dom-utils.js";
import { downloadMermaidSVG, openInMermaidLive, copyMermaidText, toggleFullscreen, downloadMermaidText } from "./mermaid-actions.js";
import { generateTableReport } from "./compressor.js";
import { generateTableDependencies, downloadTableDependenciesCSV } from "./table-analysis.js";
import {
    downloadFormulaGrapherSVG,
    openFormulaGrapherInMermaidLive,
    copyFormulaGrapherMermaidText,
    toggleFormulaGrapherFullscreen,
} from "./grapher.js";
import {
    refreshComplexityScorecard,
    sortScorecardBy,
    downloadComplexityCSV,
} from "./scorecard.js";
import {
    refreshUnusedFields,
    sortUnusedBy,
    downloadUnusedFieldsCSV,
} from "./unused.js";

type ActionHandler = (event?: Event, target?: HTMLElement) => void;

/**
 * Show the API help modal
 */
function showApiHelpModal(): void {
    const modal = document.getElementById("api-help-modal");
    if (modal) {
        modal.style.display = 'flex';
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Hide the API help modal
 */
function hideApiHelpModal(): void {
    const modal = document.getElementById("api-help-modal");
    if (modal) {
        modal.style.display = 'none';
        // Restore body scroll
        document.body.style.overflow = '';
    }
}

/**
 * Set up modal close handlers
 */
document.addEventListener("DOMContentLoaded", () => {
    const closeButton = document.getElementById("close-api-help-modal");
    const modal = document.getElementById("api-help-modal");
    
    if (closeButton) {
        closeButton.addEventListener("click", (e) => {
            e.stopPropagation();
            hideApiHelpModal();
        });
    }
    
    // Close modal when clicking the backdrop (not the content)
    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                hideApiHelpModal();
            }
        });
    }
    
    // Close modal with Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            const modal = document.getElementById("api-help-modal");
            if (modal && modal.style.display === 'flex') {
                hideApiHelpModal();
            }
        }
    });
});

/**
 * Build the action handlers registry
 */
export function buildActionHandlers(fetchSchema: () => void, loadSampleSchema: () => void): Record<string, ActionHandler> {
    return {
        "fetch-schema": fetchSchema,
        "load-sample-schema": loadSampleSchema,
        "show-api-help-modal": showApiHelpModal,
        "load-sample-schema-from-modal": () => {
            hideApiHelpModal();
            loadSampleSchema();
        },
        "download-mermaid-svg": downloadMermaidSVG,
        "open-mermaid-live": openInMermaidLive,
        "copy-mermaid": copyMermaidText,
        "toggle-mermaid-fullscreen": toggleFullscreen,
        "download-mermaid-text": downloadMermaidText,
        "generate-table-dependencies": generateTableDependencies,
        "download-table-dependencies-csv": downloadTableDependenciesCSV,
        "copy-grapher-mermaid": copyFormulaGrapherMermaidText,
        "download-grapher-svg": downloadFormulaGrapherSVG,
        "open-grapher-live": openFormulaGrapherInMermaidLive,
        "toggle-grapher-fullscreen": toggleFormulaGrapherFullscreen,
        "generate-table-report": generateTableReport,
        "copy-to-clipboard": (event, target) => {
            if (target) {
                copyToClipboard(target.dataset.target || "", target.dataset.description || "", event as MouseEvent);
            }
        },
        "refresh-scorecard": refreshComplexityScorecard,
        "sort-scorecard": (_event, target) => {
            if (target?.dataset.field) {
                sortScorecardBy(target.dataset.field as any);
            }
        },
        "download-scorecard-csv": downloadComplexityCSV,
        "refresh-unused": refreshUnusedFields,
        "sort-unused": (_event, target) => {
            if (target?.dataset.field) {
                sortUnusedBy(target.dataset.field as any);
            }
        },
        "download-unused-csv": downloadUnusedFieldsCSV,
    };
}

/**
 * Change handlers for input/select elements
 */
export const changeHandlers: Record<string, () => void> = {
    "scorecard-filter": refreshComplexityScorecard,
    "unused-filter": refreshUnusedFields,
};
