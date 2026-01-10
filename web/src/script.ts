/**
 * Main Entry Point - Application Initialization
 * Coordinates all tab modules and handles global UI state
 */

// Import web components
import './components/ui/theme-toggle.js';
import './components/ui/tab-manager.js';
import './components/ui/at-dropdown.js';

import { getDropdown, setDropdownOptions } from './modules/dom-utils.js';
import { toast } from './modules/toast.js';
import { getSchema, saveSchema } from './components/ui/schema-store.js';
import { 
    initializeCompressorDropdowns, 
    updateCompressorFieldDropdown, 
    updateOriginalFormulaDisplay,
    autoCompressFormula,
    onOutputFormatChange,
    onDisplayFormatChange
} from './modules/compressor.js';
import { 
    initializeGrapherDropdowns, 
    updateGrapherFieldDropdown, 
    onGrapherFieldSelected,
    autoGenerateFormulaGraph
} from './modules/grapher.js';
import { wireActions } from './modules/ui-events.js';
import { buildActionHandlers, changeHandlers } from './modules/action-handlers.js';
import type { DropdownOption, SchemaPayload } from './types/pyscript';

interface AirtableSchema {
    tables: Array<{
        id: string;
        name: string;
        fields: Array<{
            id: string;
            name: string;
            type: string;
            options?: Record<string, unknown>;
        }>;
    }>;
}

// Expose global functions for HTML onclick handlers
declare global {
    interface Window {
        toggleSetupAccordion: () => void;
        fetchSchemaAndUpdateUI: () => Promise<void>;
        fetchSchema: () => Promise<void>;
        loadSampleSchema: () => Promise<void>;
    }
}

/**
 * Format a timestamp as a relative time string (e.g., "2 minutes ago")
 * @param timestamp - ISO 8601 timestamp string
 */
function formatRelativeTime(timestamp: string): string {
    const now = Date.now();
    const then = new Date(timestamp).getTime();
    const diff = now - then;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
}

// Make toggleSetupAccordion available globally for HTML onclick handlers
window.toggleSetupAccordion = function(): void {
    const content = document.getElementById("setup-accordion-content");
    const arrow = document.getElementById("accordion-arrow");
    if (content && arrow) {
        const isHidden = content.classList.contains("hidden");
        if (isHidden) {
            content.classList.remove("hidden");
            arrow.style.transform = "rotate(180deg)";
        } else {
            content.classList.add("hidden");
            arrow.style.transform = "rotate(0deg)";
        }
    }
};

// Main initialization when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    // Check for existing schema and update UI accordingly
    checkSchemaAndUpdateUI();

    // Wire up action handlers for data-action buttons
    const actionHandlers = buildActionHandlers(fetchSchemaAndUpdateUI, loadSampleSchema);
    wireActions(actionHandlers, changeHandlers);

    // Set up event listeners for accordion and action buttons
    const fetchBtn = document.getElementById("fetch-schema");
    if (fetchBtn) {
        fetchBtn.addEventListener("click", fetchSchemaAndUpdateUI);
    }

    const loadSampleBtn = document.getElementById("load-sample");
    if (loadSampleBtn) {
        loadSampleBtn.addEventListener("click", loadSampleSchema);
    }

    // Wait for PyScript to be ready before wiring dropdowns
    const pyScriptReadyEvent = setInterval(() => {
        // Check if PyScript functions are available (they may be undefined initially)
        if (typeof window.parametersChanged !== 'undefined' && 
            typeof window.compressFormulaFromUI !== 'undefined' && 
            typeof window.evaluateFormulaWithValues !== 'undefined') {
            clearInterval(pyScriptReadyEvent);
            console.log('PyScript functions detected, wiring dropdowns');
            wireDropdowns();
            wireOptionControls();
        }
    }, 100);

    // Set up event listeners for formula compressor controls
    const expandFieldsCheckbox = document.getElementById('expand-fields') as HTMLInputElement | null;
    const directionSelect = document.getElementById('direction') as HTMLSelectElement | null;
    
    const controlElements = [expandFieldsCheckbox, directionSelect];
    controlElements.forEach(element => {
        if (element) {
            element.addEventListener('change', () => {
                try {
                    if (window.parametersChanged) {
                        console.log(`Calling parametersChanged from ${element.id}`);
                        window.parametersChanged();
                    }
                } catch (error) {
                    console.error('Error calling parametersChanged:', error);
                }
            });
        }
    });
    
    // Max depth uses 'input' event instead of 'change'
    const maxDepthInput = document.getElementById('max-depth') as HTMLInputElement | null;
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
    document.addEventListener('click', (event: MouseEvent) => {
        const target = event.target as HTMLElement;
        if (target.id === 'eval-calculate-btn') {
            const fieldId = target.dataset.fieldId;
            const dependenciesJson = target.dataset.dependencies;
            const outputFormatSelect = document.getElementById('eval-output-format') as HTMLSelectElement | null;
            const outputFormat = (outputFormatSelect?.value === 'field_ids' || outputFormatSelect?.value === 'field_names') 
                ? outputFormatSelect.value 
                : 'field_names' as 'field_ids' | 'field_names';
            try {
                if (fieldId && dependenciesJson) {
                    const dependencies = JSON.parse(dependenciesJson);
                    if (window.evaluateFormulaWithValues) {
                        window.evaluateFormulaWithValues(fieldId, dependencies, outputFormat);
                    } else {
                        console.warn('evaluateFormulaWithValues is not available yet');
                    }
                }
            } catch (error) {
                console.error('Error calling evaluateFormulaWithValues:', error);
            }
        }
    });
});

let fieldOptions: DropdownOption[] = [];

function checkSchemaAndUpdateUI(): void {
    const schemaData = getSchema();
    const hasSchema = !!(schemaData?.schema?.tables?.length);
    
    updateUIBasedOnSchema(hasSchema, schemaData);
    if (hasSchema) {
        updateSchemaInfo();
    }
}

function updateUIBasedOnSchema(hasSchema: boolean, schemaData: SchemaPayload | null): void {
    const setupAccordionHeader = document.getElementById("setup-accordion-header");
    const setupAccordionContent = document.getElementById("setup-accordion-content");
    const tabNavigation = document.getElementById("tab-navigation");
    const tabContent = document.getElementById("tab-content");
    const accordionRefreshDate = document.getElementById("accordion-refresh-date");
    
    if (hasSchema) {
        // Schema exists - show accordion header (collapsed), hide content, show tabs
        setupAccordionHeader?.classList.remove("hidden");
        setupAccordionContent?.classList.add("hidden");
        tabNavigation?.classList.remove("hidden");
        tabContent?.classList.remove("hidden");
        
        // Update the refresh date in the accordion header
        if (schemaData && schemaData.timestamp && accordionRefreshDate) {
            const relativeTime = formatRelativeTime(schemaData.timestamp);
            const fullDate = new Date(schemaData.timestamp).toLocaleString();
            accordionRefreshDate.textContent = `Last: ${relativeTime}`;
            accordionRefreshDate.title = fullDate;
        } else if (accordionRefreshDate) {
            accordionRefreshDate.textContent = "Last: Just now";
            accordionRefreshDate.title = new Date().toLocaleString();
        }
    } else {
        // No schema - show setup form, hide tabs
        setupAccordionHeader?.classList.add("hidden");
        setupAccordionContent?.classList.remove("hidden");
        tabNavigation?.classList.add("hidden");
        tabContent?.classList.add("hidden");
    }
}

function wireDropdowns(): void {
    const tableDropdown = getDropdown("table-dropdown");
    const fieldDropdown = getDropdown("field-dropdown");
    const compressorTableDropdown = getDropdown("compressor-table-dropdown");
    const compressorFieldDropdown = getDropdown("compressor-field-dropdown");
    const grapherTableDropdown = getDropdown("grapher-table-dropdown");
    const grapherFieldDropdown = getDropdown("grapher-field-dropdown");
    const evalTableDropdown = getDropdown("eval-table-dropdown");
    const evalFieldDropdown = getDropdown("eval-field-dropdown");

    if (tableDropdown) {
        tableDropdown.addEventListener('select', (event: Event) => {
            const customEvent = event as CustomEvent<DropdownOption>;
            if (customEvent.detail && customEvent.detail.id) {
                updateFieldDropdown(customEvent.detail.id);
            }
        });
    }

    if (fieldDropdown) {
        fieldDropdown.addEventListener('select', (event: Event) => {
            const customEvent = event as CustomEvent<DropdownOption>;
            console.log(customEvent);
            console.log(JSON.stringify(customEvent));
            if (!customEvent.detail || !customEvent.detail.tableId || !customEvent.detail.id) {
                console.warn('Field dropdown event missing required properties:', customEvent.detail);
                return;
            }
            const flowchartTypeEl = document.getElementById("flowchart-type") as HTMLSelectElement | null;
            const flowchartType = flowchartTypeEl?.value || "TD";
            // updateMermaidGraph is a PyScript function exported to window
            if (typeof window.updateMermaidGraph !== 'undefined') {
                window.updateMermaidGraph(customEvent.detail.tableId, customEvent.detail.id, flowchartType);
            }
        });
    }

    if (compressorTableDropdown) {
        compressorTableDropdown.addEventListener('select', (event: Event) => {
            const customEvent = event as CustomEvent<DropdownOption>;
            if (customEvent.detail && customEvent.detail.id) {
                updateCompressorFieldDropdown(customEvent.detail.id);
                const tableReportBtn = document.getElementById("table-report-btn") as HTMLButtonElement | null;
                if (tableReportBtn) {
                    tableReportBtn.disabled = false;
                }
            }
        });
    }

    if (compressorFieldDropdown) {
        compressorFieldDropdown.addEventListener('select', (event: Event) => {
            const customEvent = event as CustomEvent<DropdownOption>;
            if (customEvent.detail && customEvent.detail.tableId && customEvent.detail.id) {
                const formula = (customEvent.detail as { formula?: string }).formula || '';
                updateOriginalFormulaDisplay(customEvent.detail.tableId, customEvent.detail.id, formula);
            }
        });
    }

    if (grapherTableDropdown) {
        grapherTableDropdown.addEventListener('select', (event: Event) => {
            const customEvent = event as CustomEvent<DropdownOption>;
            if (customEvent.detail && customEvent.detail.id) {
                updateGrapherFieldDropdown(customEvent.detail.id);
            }
        });
    }

    if (grapherFieldDropdown) {
        grapherFieldDropdown.addEventListener('select', (event: Event) => {
            const customEvent = event as CustomEvent<DropdownOption>;
            if (customEvent.detail && customEvent.detail.tableName && customEvent.detail.text) {
                onGrapherFieldSelected(customEvent.detail.tableName, customEvent.detail.text);
            }
        });
    }

    if (evalTableDropdown) {
        evalTableDropdown.addEventListener('select', (event: Event) => {
            const customEvent = event as CustomEvent<DropdownOption>;
            if (customEvent.detail && customEvent.detail.id) {
                updateEvalFieldDropdown(customEvent.detail.id);
            }
        });
    }

    if (evalFieldDropdown) {
        evalFieldDropdown.addEventListener('select', (event: Event) => {
            const customEvent = event as CustomEvent<DropdownOption>;
            if (customEvent.detail && customEvent.detail.id) {
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
}

/**
 * Wire up option controls (selects, checkboxes) to trigger updates
 */
function wireOptionControls(): void {
    // Dependency Mapper controls
    const flowchartTypeEl = document.getElementById('flowchart-type') as HTMLSelectElement | null;
    const graphDirectionEl = document.getElementById('graph-direction') as HTMLSelectElement | null;
    const maxDepthEl = document.getElementById('max-depth') as HTMLInputElement | null;
    const descriptionDisplayModeEl = document.getElementById('description-display-mode') as HTMLSelectElement | null;

    // When any dependency mapper control changes, re-generate the graph
    [flowchartTypeEl, graphDirectionEl, maxDepthEl, descriptionDisplayModeEl].forEach(element => {
        if (element) {
            element.addEventListener('change', () => {
                const fieldDropdown = getDropdown('field-dropdown');
                // const tableDropdown = getDropdown('table-dropdown');
                
                // Get the selected option which contains all the data (id, text, tableId)
                const selectedField = fieldDropdown?.selectedOption;
                // const selectedTable = tableDropdown?.selectedOption;
                
                if (selectedField && selectedField.id && selectedField.tableId) {
                    const flowchartType = flowchartTypeEl?.value || 'TD';
                    
                    if (typeof window.updateMermaidGraph !== 'undefined') {
                        window.updateMermaidGraph(selectedField.tableId, selectedField.id, flowchartType);
                    }
                }
            });
        }
    });

    // Formula Grapher controls
    const grapherExpandFieldsEl = document.getElementById('grapher-expand-fields') as HTMLInputElement | null;
    const grapherExpansionDepthEl = document.getElementById('grapher-expansion-depth') as HTMLInputElement | null;
    const grapherFlowchartDirectionEl = document.getElementById('grapher-flowchart-direction') as HTMLSelectElement | null;

    [grapherExpandFieldsEl, grapherFlowchartDirectionEl].forEach(element => {
        if (element) {
            element.addEventListener('change', () => {
                autoGenerateFormulaGraph();
            });
        }
    });

    if (grapherExpansionDepthEl) {
        grapherExpansionDepthEl.addEventListener('input', () => {
            autoGenerateFormulaGraph();
        });
    }

    // Formula Compressor controls
    const compressionDepthEl = document.getElementById('compression-depth') as HTMLInputElement | null;
    const outputFormatEl = document.getElementById('output-format') as HTMLSelectElement | null;
    const displayFormatEl = document.getElementById('display-format') as HTMLSelectElement | null;
    
    if (compressionDepthEl) {
        compressionDepthEl.addEventListener('input', () => {
            autoCompressFormula();
        });
    }
    
    if (outputFormatEl) {
        outputFormatEl.addEventListener('change', () => {
            onOutputFormatChange();
        });
    }
    
    if (displayFormatEl) {
        displayFormatEl.addEventListener('change', () => {
            onDisplayFormatChange();
        });
    }
}

async function fetchSchemaAndUpdateUI(): Promise<void> {
    const baseIdEl = document.getElementById("base-id") as HTMLInputElement | null;
    const patEl = document.getElementById("pat") as HTMLInputElement | null;
    
    const baseId = baseIdEl?.value;
    const pat = patEl?.value;
    
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
        const schema = await response.json() as AirtableSchema;
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
async function fetchSchema(): Promise<void> {
    return fetchSchemaAndUpdateUI();
}

async function loadSampleSchema(): Promise<void> {
    try {
        const response = await fetch('./sample_schema.json');
        if (!response.ok) {
            throw new Error(`Failed to load sample schema: ${response.statusText}`);
        }
        const schema = await response.json() as AirtableSchema;
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

function updateSchemaInfo(): void {
    const schemaData = getSchema();
    const tables = schemaData?.schema?.tables || [];
    
    // Update last refresh with relative time and tooltip
    const lastRefreshElement = document.getElementById("last-refresh");
    if (schemaData && schemaData.timestamp && lastRefreshElement) {
        const relativeTime = formatRelativeTime(schemaData.timestamp);
        const fullDate = new Date(schemaData.timestamp).toLocaleString();
        lastRefreshElement.textContent = `Last Refresh: ${relativeTime}`;
        lastRefreshElement.title = fullDate;
    } else if (schemaData && lastRefreshElement) {
        lastRefreshElement.textContent = "Last Refresh: Just now";
        lastRefreshElement.title = new Date().toLocaleString();
    } else if (lastRefreshElement) {
        lastRefreshElement.textContent = "Last Refresh: Not yet retrieved";
        lastRefreshElement.title = "";
    }

    const tableOptions: DropdownOption[] = tables.map(table => ({
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
    const tableDepsBtn = document.getElementById("generate-table-dependencies-btn") as HTMLButtonElement | null;
    if (tableDepsBtn && tables.length > 0) {
        tableDepsBtn.disabled = false;
    }
}

function updateFieldDropdown(tableId: string): void {
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
    if (specialOption) {
        fieldOptions.sort((a, b) => a.text.localeCompare(b.text));
        fieldOptions.unshift(specialOption);
    }

    if (fieldDropdown) {
        fieldDropdown.value = "";
    }

    setDropdownOptions("field-dropdown", fieldOptions);
}

function updateEvalFieldDropdown(tableId: string): void {
    const schemaData = getSchema();
    const evalFieldDropdown = getDropdown("eval-field-dropdown");
    const fieldOptions: DropdownOption[] = [];

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

// Export functions that are called from HTML
window.fetchSchemaAndUpdateUI = fetchSchemaAndUpdateUI;
window.fetchSchema = fetchSchema;
window.loadSampleSchema = loadSampleSchema;
