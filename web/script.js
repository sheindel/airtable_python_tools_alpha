import "./components/ui/at-dropdown.js";
import "./components/ui/theme-toggle.js";
import "./components/ui/tab-manager.js";
import { saveSchema, getSchema } from "./components/ui/schema-store.js";
import { getDropdown, setDropdownOptions, formatRelativeTime } from "./modules/dom-utils.js";
import { toast } from "./modules/toast.js";
import {
    updateCompressorFieldDropdown,
    updateOriginalFormulaDisplay,
    onOutputFormatChange,
    onDisplayFormatChange,
    initializeCompressorDropdowns
} from "./modules/compressor.js";
import {
    initializeAnalysisDropdowns
} from "./modules/table-analysis.js";
import {
    initializeGrapherDropdowns,
    updateGrapherFieldDropdown,
    onGrapherFieldSelected
} from "./modules/grapher.js";
import {
    initializeScorecardDropdowns,
} from "./modules/scorecard.js";
import {
    initializeUnusedDropdowns,
} from "./modules/unused.js";
import { wireActions } from "./modules/ui-events.js";
import { buildActionHandlers, changeHandlers } from "./modules/action-handlers.js";

document.addEventListener("DOMContentLoaded", () => {
    checkSchemaAndUpdateUI();
    wireDropdowns();
    const actionHandlers = buildActionHandlers(fetchSchemaAndUpdateUI, loadSampleSchema);
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

    // Handle dynamically created eval-calculate-btn
    document.addEventListener('click', (event) => {
        if (event.target.id === 'eval-calculate-btn') {
            const fieldId = event.target.dataset.fieldId;
            const dependenciesJson = event.target.dataset.dependencies;
            const outputFormatSelect = document.getElementById('eval-output-format');
            const outputFormat = outputFormatSelect ? outputFormatSelect.value : 'field_names';
            try {
                const dependencies = JSON.parse(dependenciesJson);
                if (window.evaluateFormulaWithValues) {
                    window.evaluateFormulaWithValues(fieldId, dependencies, outputFormat);
                } else {
                    console.warn('evaluateFormulaWithValues is not available yet');
                }
            } catch (error) {
                console.error('Error calling evaluateFormulaWithValues:', error);
            }
        }
    });
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
            const relativeTime = formatRelativeTime(schemaData.timestamp);
            const fullDate = new Date(schemaData.timestamp).toLocaleString();
            accordionRefreshDate.textContent = `Last: ${relativeTime}`;
            accordionRefreshDate.title = fullDate;
        } else {
            accordionRefreshDate.textContent = "Last: Just now";
            accordionRefreshDate.title = new Date().toLocaleString();
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
    const grapherTableDropdown = getDropdown("grapher-table-dropdown");
    const grapherFieldDropdown = getDropdown("grapher-field-dropdown");
    const evalTableDropdown = getDropdown("eval-table-dropdown");
    const evalFieldDropdown = getDropdown("eval-field-dropdown");
    const evaluatorTableDropdown = getDropdown("evaluator-table-dropdown");

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

    if (evalTableDropdown) {
        evalTableDropdown.addEventListener('select', (event) => {
            if (event.detail && event.detail.id) {
                updateEvalFieldDropdown(event.detail.id);
            }
        });
    }

    if (evalFieldDropdown) {
        evalFieldDropdown.addEventListener('select', (event) => {
            if (event.detail && event.detail.id) {
                try {
                    if (window.loadFieldDependencies) {
                        window.loadFieldDependencies();
                    } else {
                        console.warn('loadFieldDependencies is not available yet');
                    }
                } catch (error) {
                    console.error('Error calling loadFieldDependencies:', error);
                }
            }
        });
    }

    // Evaluator Generator tab dropdown (table selection only)
    if (evaluatorTableDropdown) {
        evaluatorTableDropdown.addEventListener('select', (event) => {
            if (event.detail && event.detail.id) {
                console.log('Evaluator table selected:', event.detail.text);
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
        toast.warning("Please enter both Base ID and PAT.");
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
        toast.error("Failed to retrieve schema.");
    }
}

// Keep the old function name for backward compatibility
async function fetchSchema() {
    return fetchSchemaAndUpdateUI();
}

async function loadSampleSchema() {
    try {
        const response = await fetch('./sample_schema.json');
        if (!response.ok) {
            throw new Error(`Failed to load sample schema: ${response.statusText}`);
        }
        const schema = await response.json();
        saveSchema(schema);
        
        // Update UI after loading sample schema
        const schemaData = getSchema();
        updateUIBasedOnSchema(true, schemaData);
        updateSchemaInfo();
        
        toast.success("Sample schema loaded successfully!");
    } catch (error) {
        console.error("Error loading sample schema:", error);
        toast.error("Failed to load sample schema. Please check the console for details.");
    }
}

function updateSchemaInfo() {
    const schemaData = getSchema();
    const tables = schemaData?.schema?.tables || [];
    
    // Update last refresh with relative time and tooltip
    const lastRefreshElement = document.getElementById("last-refresh");
    if (schemaData && schemaData.timestamp) {
        const relativeTime = formatRelativeTime(schemaData.timestamp);
        const fullDate = new Date(schemaData.timestamp).toLocaleString();
        lastRefreshElement.textContent = `Last Refresh: ${relativeTime}`;
        lastRefreshElement.title = fullDate;
    } else if (schemaData) {
        lastRefreshElement.textContent = "Last Refresh: Just now";
        lastRefreshElement.title = new Date().toLocaleString();
    } else {
        lastRefreshElement.textContent = "Last Refresh: Not yet retrieved";
        lastRefreshElement.title = "";
    }

    const tableOptions = tables.map(table => ({
        id: table.id,
        text: table.name,
        table
    }));

    tableOptions.sort((a, b) => a.text.localeCompare(b.text));
    setDropdownOptions("table-dropdown", tableOptions);
    setDropdownOptions("eval-table-dropdown", tableOptions);
    setDropdownOptions("evaluator-table-dropdown", tableOptions);
    initializeCompressorDropdowns();
    initializeGrapherDropdowns();
    
    // Enable table dependencies button (doesn't require dropdown selection)
    const tableDepsBtn = document.getElementById("generate-table-dependencies-btn");
    if (tableDepsBtn && tables.length > 0) {
        tableDepsBtn.disabled = false;
    }
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

function updateEvalFieldDropdown(tableId) {
    const schemaData = getSchema();
    const evalFieldDropdown = getDropdown("eval-field-dropdown");
    const fieldOptions = [];

    const selectedTable = schemaData?.schema?.tables?.find(table => table.id === tableId);
    selectedTable?.fields.forEach(field => {
        // Only include formula and rollup fields
        if (field.type === "formula" || field.type === "rollup") {
            fieldOptions.push({
                id: field.id,
                text: field.name,
                tableId
            });
        }
    });

    fieldOptions.sort((a, b) => a.text.localeCompare(b.text));

    if (evalFieldDropdown) {
        evalFieldDropdown.value = "";
    }

    setDropdownOptions("eval-field-dropdown", fieldOptions);
}

// Global function for types generator tab (called from HTML onchange)
window.updateTypeOptions = function() {
    const languageSelect = document.getElementById("types-language");
    const sqlDialectContainer = document.getElementById("sql-dialect-container");
    const helperTypesContainer = document.getElementById("helper-types-container");
    const sqlOptionsContainer = document.getElementById("sql-options-container");
    
    if (!languageSelect) return;
    
    const language = languageSelect.value;
    const isSql = language === "sql-functions" || language === "sql-triggers";
    
    // Show/hide SQL dialect selection
    if (sqlDialectContainer) {
        if (isSql) {
            sqlDialectContainer.classList.remove("hidden");
        } else {
            sqlDialectContainer.classList.add("hidden");
        }
    }
    
    // Show/hide helper types checkbox (TypeScript/Python only)
    if (helperTypesContainer) {
        if (isSql) {
            helperTypesContainer.classList.add("hidden");
        } else {
            helperTypesContainer.classList.remove("hidden");
        }
    }
    
    // Show/hide SQL options (SQL only)
    if (sqlOptionsContainer) {
        if (isSql) {
            sqlOptionsContainer.classList.remove("hidden");
        } else {
            sqlOptionsContainer.classList.add("hidden");
        }
    }
}
