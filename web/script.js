import "./components/ui/at-dropdown.js";
import "./components/ui/theme-toggle.js";
import "./components/ui/tab-manager.js";
import { saveSchema, getSchema, getTables } from "./components/ui/schema-store.js";
import { getDropdown, setDropdownOptions, copyToClipboard } from "./modules/dom-utils.js";
import { downloadMermaidSVG, openInMermaidLive, copyMermaidText, toggleFullscreen, downloadMermaidText } from "./modules/mermaid-actions.js";
import {
    updateCompressorFieldDropdown,
    updateOriginalFormulaDisplay,
    updateOriginalFormulaFormat,
    onOutputFormatChange,
    onDisplayFormatChange,
    compressFormula,
    autoCompressFormula,
    copyCompressedFormula,
    generateTableReport,
    initializeCompressorDropdowns
} from "./modules/compressor.js";
import {
    initializeAnalysisDropdowns,
    generateTableComplexityCSV,
    downloadTableComplexityCSV
} from "./modules/table-analysis.js";
import {
    initializeGrapherDropdowns,
    updateGrapherFieldDropdown,
    onGrapherFieldSelected,
    autoGenerateFormulaGraph,
    downloadFormulaGrapherSVG,
    openFormulaGrapherInMermaidLive,
    copyFormulaGrapherMermaidText,
    toggleFormulaGrapherFullscreen
} from "./modules/grapher.js";
import {
    initializeScorecardDropdowns,
    refreshComplexityScorecard,
    sortScorecardBy,
    downloadComplexityCSV
} from "./modules/scorecard.js";
import {
    initializeUnusedDropdowns,
    refreshUnusedFields,
    sortUnusedBy,
    downloadUnusedFieldsCSV
} from "./modules/unused.js";
import { wireActions } from "./modules/ui-events.js";

const actionHandlers = {
    "fetch-schema": fetchSchema,
    "download-mermaid-svg": downloadMermaidSVG,
    "open-mermaid-live": openInMermaidLive,
    "copy-mermaid": copyMermaidText,
    "toggle-mermaid-fullscreen": toggleFullscreen,
    "download-mermaid-text": downloadMermaidText,
    "generate-table-complexity": generateTableComplexityCSV,
    "download-table-complexity": downloadTableComplexityCSV,
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

const changeHandlers = {
    "scorecard-filter": refreshComplexityScorecard,
    "unused-filter": refreshUnusedFields,
};

document.addEventListener("DOMContentLoaded", () => {
    hydrateSchemaFromStorage();
    wireDropdowns();
    wireActions(actionHandlers, changeHandlers);

    document.addEventListener("tab-change", (event) => {
        const tabName = event.detail?.tab;
        if (!tabName) return;

        if (tabName === "complexity-scorecard") {
            initializeScorecardDropdowns();
        } else if (tabName === "unused-fields") {
            initializeUnusedDropdowns();
        }
    });
});

// Wait for PyScript to be ready before calling Python functions
addEventListener('py:ready', () => {
    console.log('PyScript is ready - tabs initialized');
    
    // Add event listener for output format changes
    const outputFormatSelect = document.getElementById("output-format");
    if (outputFormatSelect) {
        outputFormatSelect.addEventListener("change", onOutputFormatChange);
    }
    
    // Add event listener for display format changes
    const displayFormatSelect = document.getElementById("display-format");
    if (displayFormatSelect) {
        displayFormatSelect.addEventListener("change", onDisplayFormatChange);
    }
});

let fieldOptions = [];

function hydrateSchemaFromStorage() {
    updateSchemaInfo();
}

function wireDropdowns() {
    const tableDropdown = getDropdown("table-dropdown");
    const fieldDropdown = getDropdown("field-dropdown");
    const compressorTableDropdown = getDropdown("compressor-table-dropdown");
    const compressorFieldDropdown = getDropdown("compressor-field-dropdown");
    const analysisTableDropdown = getDropdown("analysis-table-dropdown");
    const grapherTableDropdown = getDropdown("grapher-table-dropdown");
    const grapherFieldDropdown = getDropdown("grapher-field-dropdown");

    if (tableDropdown) {
        tableDropdown.addEventListener('select', (event) => {
            updateFieldDropdown(event.detail.id);
        });
    }

    if (fieldDropdown) {
        fieldDropdown.addEventListener('select', (event) => {
            const flowchartType = document.getElementById("flowchart-type")?.value || "TD";
            if (typeof updateMermaidGraph !== 'undefined') {
                updateMermaidGraph(event.detail.tableId, event.detail.id, flowchartType);
            }
        });
    }

    if (compressorTableDropdown) {
        compressorTableDropdown.addEventListener('select', (event) => {
            updateCompressorFieldDropdown(event.detail.id);
            const tableReportBtn = document.getElementById("table-report-btn");
            if (tableReportBtn) {
                tableReportBtn.disabled = false;
            }
        });
    }

    if (compressorFieldDropdown) {
        compressorFieldDropdown.addEventListener('select', (event) => {
            updateOriginalFormulaDisplay(event.detail.tableId, event.detail.id, event.detail.formula);
        });
    }

    if (analysisTableDropdown) {
        analysisTableDropdown.addEventListener('select', () => {
            const generateBtn = document.getElementById("generate-table-complexity-btn");
            if (generateBtn) {
                generateBtn.disabled = false;
            }
        });
    }

    if (grapherTableDropdown) {
        grapherTableDropdown.addEventListener('select', (event) => {
            updateGrapherFieldDropdown(event.detail.id);
        });
    }

    if (grapherFieldDropdown) {
        grapherFieldDropdown.addEventListener('select', (event) => {
            onGrapherFieldSelected(event.detail.tableName, event.detail.text);
        });
    }
}

function setActiveTab(tabName) {
    const manager = document.querySelector('at-tab-manager');
    manager?.setActive(tabName, true);
}

async function fetchSchema() {
    const baseId = document.getElementById("base-id").value;
    const pat = document.getElementById("pat").value;
    if (!baseId || !pat) {
        alert("Please enter both Base ID and PAT.");
        return;
    }
    try {
        const response = await fetch(`https://api.airtable.com/v0/meta/bases/${baseId}/tables`, {
            headers: {
                Authorization: `Bearer ${pat}`,
                "Content-Type": "application/json"
            }
        });
        const schema = await response.json();
        saveSchema(schema);
        updateSchemaInfo();
    } catch (error) {
        console.error("Error fetching schema:", error);
        alert("Failed to retrieve schema.");
    }
}

function updateSchemaInfo() {
    const schemaData = getSchema();
    const tables = schemaData?.schema?.tables || [];
    document.getElementById("last-refresh").textContent = schemaData ? `Last Refresh: ${schemaData.timestamp || "Just now"}` : "Last Refresh: Not yet retrieved";

    const tableOptions = tables.map(table => ({
        id: table.id,
        text: table.name,
        table
    }));

    tableOptions.sort((a, b) => a.text.localeCompare(b.text));
    setDropdownOptions("table-dropdown", tableOptions);
    initializeCompressorDropdowns();
    initializeAnalysisDropdowns();
    initializeGrapherDropdowns();
}

function updateFieldDropdown(tableId) {
    const schemaData = getSchema();
    const fieldDropdown = getDropdown("field-dropdown");
    fieldOptions = [];

    fieldOptions.push({
        id: "__TABLE_DEPENDENCIES__",
        text: "<Show Table Dependencies>",
        tableId
    });

    const selectedTable = schemaData?.schema?.tables?.find(table => table.id === tableId);
    selectedTable?.fields.forEach(field => {
        fieldOptions.push({
            id: field.id,
            text: field.name,
            tableId
        });
    });

    const specialOption = fieldOptions.shift();
    fieldOptions.sort((a, b) => a.text.localeCompare(b.text));
    fieldOptions.unshift(specialOption);

    if (fieldDropdown) {
        fieldDropdown.value = "";
    }

    setDropdownOptions("field-dropdown", fieldOptions);
}

// Export functions to window object so they can be called from HTML
window.fetchSchema = fetchSchema;
window.downloadMermaidSVG = downloadMermaidSVG;
window.openInMermaidLive = openInMermaidLive;
window.copyMermaidText = copyMermaidText;
window.toggleFullscreen = toggleFullscreen;
window.downloadMermaidText = downloadMermaidText;
window.switchTab = setActiveTab;
window.compressFormula = compressFormula;
window.copyCompressedFormula = copyCompressedFormula;
window.generateTableReport = generateTableReport;
window.copyToClipboard = copyToClipboard;
window.generateTableComplexityCSV = generateTableComplexityCSV;
window.downloadTableComplexityCSV = downloadTableComplexityCSV;
window.downloadFormulaGrapherSVG = downloadFormulaGrapherSVG;
window.openFormulaGrapherInMermaidLive = openFormulaGrapherInMermaidLive;
window.copyFormulaGrapherMermaidText = copyFormulaGrapherMermaidText;
window.toggleFormulaGrapherFullscreen = toggleFormulaGrapherFullscreen;
window.refreshComplexityScorecard = refreshComplexityScorecard;
window.sortScorecardBy = sortScorecardBy;
window.downloadComplexityCSV = downloadComplexityCSV;
window.refreshUnusedFields = refreshUnusedFields;
window.sortUnusedBy = sortUnusedBy;
window.downloadUnusedFieldsCSV = downloadUnusedFieldsCSV;
