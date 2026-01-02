/**
 * Formula Grapher Module
 * Handles the Formula Grapher tab logic, including dropdown initialization,
 * field selection, and diagram generation with PyScript integration.
 */

import { getSchema, getTables } from "../components/ui/schema-store.js";
import { getDropdown, setDropdownOptions } from "./dom-utils.js";
import { toast } from "./toast.js";
import type { AirtableTable, DropdownOption } from "../types/pyscript.js";
import type { AtDropdownElement } from "../types/dom.js";

interface GrapherFieldOption extends DropdownOption {
    tableName: string;
    formula: string;
}

let grapherTableOptions: DropdownOption[] = [];
let grapherFieldOptions: GrapherFieldOption[] = [];

/**
 * Initialize the grapher dropdowns with table options
 */
export function initializeGrapherDropdowns(): void {
    const tables = getTables();
    grapherTableOptions = tables.map((table: AirtableTable) => ({ id: table.id, text: table.name }));
    grapherFieldOptions = [];

    grapherTableOptions.sort((a, b) => a.text.localeCompare(b.text));
    setDropdownOptions("grapher-table-dropdown", grapherTableOptions);
    setDropdownOptions("grapher-field-dropdown", []);
}

/**
 * Update field dropdown when a table is selected
 */
export function updateGrapherFieldDropdown(tableId: string): void {
    const schemaData = getSchema();
    const fieldDropdown = getDropdown("grapher-field-dropdown");
    grapherFieldOptions = [];

    let tableName = "";
    const selectedTable = schemaData?.schema?.tables?.find((table) => table.id === tableId);
    if (selectedTable) {
        tableName = selectedTable.name;
        selectedTable.fields.forEach((field) => {
            if (field.type === "formula") {
                grapherFieldOptions.push({
                    id: field.id,
                    text: field.name,
                    tableId,
                    tableName,
                    formula: field.options?.formula || "",
                });
            }
        });
    }

    grapherFieldOptions.sort((a, b) => a.text.localeCompare(b.text));
    if (fieldDropdown) {
        fieldDropdown.value = "";
    }
    setDropdownOptions("grapher-field-dropdown", grapherFieldOptions);

    const formulaDisplay = document.getElementById("grapher-formula-display");
    const mermaidContainer = document.getElementById("formula-grapher-mermaid-container");
    if (formulaDisplay) {
        formulaDisplay.innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">Select a formula field to see its formula</span>';
    }
    if (mermaidContainer) {
        mermaidContainer.innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">Select a formula field to generate flowchart</span>';
    }
}

/**
 * Handle field selection and display formula
 */
export function onGrapherFieldSelected(tableName: string, fieldName: string): void {
    if (typeof window.getFormulaForDisplay !== "undefined") {
        const formula = window.getFormulaForDisplay(tableName, fieldName);
        const formulaDisplay = document.getElementById("grapher-formula-display");
        if (formulaDisplay) {
            if (formula) {
                formulaDisplay.innerHTML = `<span class="text-gray-900 dark:text-gray-100">${formula.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>`;
            } else {
                formulaDisplay.innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">No formula available</span>';
            }
        }
    }

    autoGenerateFormulaGraph();
}

/**
 * Automatically generate formula graph based on current selections
 */
export function autoGenerateFormulaGraph(): void {
    const tableInput = document.getElementById("grapher-table-dropdown") as AtDropdownElement | null;
    const fieldInput = document.getElementById("grapher-field-dropdown") as AtDropdownElement | null;

    const tableName = tableInput ? tableInput.value.trim() : "";
    const fieldName = fieldInput ? fieldInput.value.trim() : "";

    if (!tableName || !fieldName) {
        return;
    }

    const expandCheckbox = document.getElementById("grapher-expand-fields") as HTMLInputElement | null;
    const depthInput = document.getElementById("grapher-expansion-depth") as HTMLInputElement | null;
    const directionDropdown = document.getElementById("grapher-flowchart-direction") as HTMLSelectElement | null;

    const expandFields = !!expandCheckbox?.checked;
    const direction = directionDropdown ? directionDropdown.value : "TD";
    const depthValue = depthInput ? depthInput.value.trim() : "1";
    const maxDepth = depthValue ? parseInt(depthValue, 10) : 1;

    if (typeof window.graphFormulaFromUI !== "undefined") {
        window.graphFormulaFromUI(tableName, fieldName, expandFields, maxDepth, direction);
    }
}

/**
 * Download the formula graph as SVG
 */
export function downloadFormulaGrapherSVG(): void {
    const svgElement = document.querySelector("#formula-grapher-mermaid-container .mermaid svg") as SVGSVGElement | null;
    if (!svgElement) return toast.warning("No diagram available to download");
    
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: "image/svg+xml" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "formula_flowchart.svg";
    link.click();
}

/**
 * Open the formula graph in Mermaid Live Editor
 */
export function openFormulaGrapherInMermaidLive(): void {
    const graphDefinition = localStorage.getItem("lastFormulaGraphDefinition");
    if (!graphDefinition) return toast.warning("No diagram available to open in Mermaid Live");

    const state = {
        code: graphDefinition,
        mermaid: "{\n  \"theme\": \"default\"\n}",
        autoSync: true,
        rough: false,
        updateDiagram: false,
        panZoom: true,
        pan: "",
        zoom: "",
        editorMode: "code",
    };
    
    // Using pako and Base64 from window (loaded externally)
    const compressedGraph = (window as any).pako.deflate(new TextEncoder().encode(JSON.stringify(state)), { level: 9 });
    const encodedGraph = (window as any).Base64.fromUint8Array(compressedGraph, true);
    const mermaidLiveUrl = `https://mermaid.live/edit#pako:${encodedGraph}`;
    window.open(mermaidLiveUrl, "_blank");
}

/**
 * Copy the formula graph Mermaid text to clipboard
 */
export function copyFormulaGrapherMermaidText(): void {
    const graphDefinition = localStorage.getItem("lastFormulaGraphDefinition");
    if (!graphDefinition) return toast.warning("No diagram available to copy");
    
    navigator.clipboard.writeText(graphDefinition).then(() => {
        toast.success("Mermaid diagram copied to clipboard");
    }).catch((error: Error) => {
        console.error("Error copying to clipboard:", error);
        toast.error("Failed to copy Mermaid diagram to clipboard");
    });
}

/**
 * Toggle fullscreen mode for the formula graph container
 */
export function toggleFormulaGrapherFullscreen(): void {
    const mermaidContainer = document.getElementById("formula-grapher-mermaid-container");
    if (!document.fullscreenElement) {
        mermaidContainer?.requestFullscreen().catch((err: Error) => {
            toast.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
        });
    } else {
        document.exitFullscreen();
    }
}
