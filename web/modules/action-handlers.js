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

// Modal helper functions
function showApiHelpModal() {
    const modal = document.getElementById("api-help-modal");
    if (modal) {
        modal.style.display = 'flex';
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
    }
}

function hideApiHelpModal() {
    const modal = document.getElementById("api-help-modal");
    if (modal) {
        modal.style.display = 'none';
        // Restore body scroll
        document.body.style.overflow = '';
    }
}

// Set up modal close handlers
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

export function buildActionHandlers(fetchSchema, loadSampleSchema) {
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
        "copy-to-clipboard": (event, target) => copyToClipboard(target.dataset.target, target.dataset.description || "", event),
        "refresh-scorecard": refreshComplexityScorecard,
        "sort-scorecard": (_event, target) => sortScorecardBy(target.dataset.field),
        "download-scorecard-csv": downloadComplexityCSV,
        "refresh-unused": refreshUnusedFields,
        "sort-unused": (_event, target) => sortUnusedBy(target.dataset.field),
        "download-unused-csv": downloadUnusedFieldsCSV,
    };
}

export const changeHandlers = {
    "scorecard-filter": refreshComplexityScorecard,
    "unused-filter": refreshUnusedFields,
};
