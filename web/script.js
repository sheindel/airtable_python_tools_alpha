import "./components/ui/at-dropdown.js";
import "./components/ui/theme-toggle.js";
import "./components/ui/tab-manager.js";
import { saveSchema, getSchema, getTables } from "./components/ui/schema-store.js";
import { getDropdown, setDropdownOptions } from "./modules/dom-utils.js";
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
import { buildActionHandlers, changeHandlers } from "./modules/action-handlers.js";

document.addEventListener("DOMContentLoaded", () => {
    checkSchemaAndUpdateUI();
    wireDropdowns();
    const actionHandlers = buildActionHandlers(fetchSchemaAndUpdateUI);
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

// Global function for accordion toggle (called from HTML onclick)
window.toggleSetupAccordion = function() {
    const accordionContent = document.getElementById("setup-accordion-content");
    const accordionHeader = document.getElementById("setup-accordion-header");
    const accordionArrow = document.getElementById("accordion-arrow");
    
    const isExpanded = !accordionContent.classList.contains("hidden");
    
    if (isExpanded) {
        // Collapse
        accordionContent.classList.add("hidden");
        accordionArrow.classList.remove("rotate-180");
    } else {
        // Expand
        accordionContent.classList.remove("hidden");
        accordionArrow.classList.add("rotate-180");
    }
};

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
    
    // Wire up dependency mapper controls to call Python function
    const dependencyMapperControls = [
        'field-dropdown',
        'flowchart-type',
        'graph-direction',
        'description-display-mode'
    ];
    
    dependencyMapperControls.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', () => {
                try {
                    if (window.parametersChanged) {
                        console.log(`Calling parametersChanged from ${id}`);
                        window.parametersChanged();
                    }
                } catch (error) {
                    console.error('Error calling parametersChanged:', error);
                }
            });
        }
    });
    
    // Max depth uses 'input' event instead of 'change'
    const maxDepthInput = document.getElementById('max-depth');
    if (maxDepthInput) {
        maxDepthInput.addEventListener('input', () => {
            try {
                if (window.parametersChanged) {
                    console.log('Calling parametersChanged from max-depth');
                    window.parametersChanged();
                }
            } catch (error) {
                console.error('Error calling parametersChanged:', error);
            }
        });
    }
});

let fieldOptions = [];

function checkSchemaAndUpdateUI() {
    const schemaData = getSchema();
    const hasSchema = schemaData && schemaData.schema && schemaData.schema.tables && schemaData.schema.tables.length > 0;
    
    updateUIBasedOnSchema(hasSchema, schemaData);
    if (hasSchema) {
        updateSchemaInfo();
    }
}

function updateUIBasedOnSchema(hasSchema, schemaData) {
    const setupAccordionHeader = document.getElementById("setup-accordion-header");
    const setupAccordionContent = document.getElementById("setup-accordion-content");
    const tabNavigation = document.getElementById("tab-navigation");
    const tabContent = document.getElementById("tab-content");
    const accordionRefreshDate = document.getElementById("accordion-refresh-date");
    
    if (hasSchema) {
        // Schema exists - show accordion header (collapsed), hide content, show tabs
        setupAccordionHeader.classList.remove("hidden");
        setupAccordionContent.classList.add("hidden");
        tabNavigation.classList.remove("hidden");
        tabContent.classList.remove("hidden");
        
        // Update the refresh date in the accordion header
        if (schemaData && schemaData.timestamp) {
            accordionRefreshDate.textContent = `Last: ${schemaData.timestamp}`;
        } else {
            accordionRefreshDate.textContent = "Last: Just now";
        }
    } else {
        // No schema - show setup form, hide tabs
        setupAccordionHeader.classList.add("hidden");
        setupAccordionContent.classList.remove("hidden");
        tabNavigation.classList.add("hidden");
        tabContent.classList.add("hidden");
    }
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
            if (event.detail && event.detail.id) {
                updateFieldDropdown(event.detail.id);
            }
        });
    }

    if (fieldDropdown) {
        fieldDropdown.addEventListener('select', (event) => {
            console.log(event);
            console.log(JSON.stringify(event));
            if (!event.detail || !event.detail.tableId || !event.detail.id) {
                console.warn('Field dropdown event missing required properties:', event.detail);
                return;
            }
            const flowchartType = document.getElementById("flowchart-type")?.value || "TD";
            if (typeof updateMermaidGraph !== 'undefined') {
                updateMermaidGraph(event.detail.tableId, event.detail.id, flowchartType);
            }
        });
    }

    if (compressorTableDropdown) {
        compressorTableDropdown.addEventListener('select', (event) => {
            if (event.detail && event.detail.id) {
                updateCompressorFieldDropdown(event.detail.id);
                const tableReportBtn = document.getElementById("table-report-btn");
                if (tableReportBtn) {
                    tableReportBtn.disabled = false;
                }
            }
        });
    }

    if (compressorFieldDropdown) {
        compressorFieldDropdown.addEventListener('select', (event) => {
            if (event.detail && event.detail.tableId && event.detail.id) {
                updateOriginalFormulaDisplay(event.detail.tableId, event.detail.id, event.detail.formula);
            }
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
            if (event.detail && event.detail.id) {
                updateGrapherFieldDropdown(event.detail.id);
            }
        });
    }

    if (grapherFieldDropdown) {
        grapherFieldDropdown.addEventListener('select', (event) => {
            if (event.detail && event.detail.tableName && event.detail.text) {
                onGrapherFieldSelected(event.detail.tableName, event.detail.text);
            }
        });
    }
}

function setActiveTab(tabName) {
    const manager = document.querySelector('at-tab-manager');
    manager?.setActive(tabName, true);
}

async function fetchSchemaAndUpdateUI() {
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
        
        // Update UI after fetching schema
        const schemaData = getSchema();
        updateUIBasedOnSchema(true, schemaData);
        updateSchemaInfo();
    } catch (error) {
        console.error("Error fetching schema:", error);
        alert("Failed to retrieve schema.");
    }
}

// Keep the old function name for backward compatibility
async function fetchSchema() {
    return fetchSchemaAndUpdateUI();
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
