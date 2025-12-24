import { getSchema, getTables } from "../components/ui/schema-store.js";
import { getDropdown, setDropdownOptions } from "./dom-utils.js";
import { toast } from "./toast.js";

let grapherTableOptions = [];
let grapherFieldOptions = [];

export function initializeGrapherDropdowns() {
    const tables = getTables();
    grapherTableOptions = tables.map((table) => ({ id: table.id, text: table.name }));
    grapherFieldOptions = [];

    grapherTableOptions.sort((a, b) => a.text.localeCompare(b.text));
    setDropdownOptions("grapher-table-dropdown", grapherTableOptions);
    setDropdownOptions("grapher-field-dropdown", []);
}

export function updateGrapherFieldDropdown(tableId) {
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

export function onGrapherFieldSelected(tableName, fieldName) {
    if (typeof window.getFormulaForDisplay !== "undefined") {
        const formula = window.getFormulaForDisplay(tableName, fieldName);
        const formulaDisplay = document.getElementById("grapher-formula-display");
        if (formulaDisplay) {
            if (formula) {
                formulaDisplay.textContent = formula;
            } else {
                formulaDisplay.innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">No formula available</span>';
            }
        }
    }

    autoGenerateFormulaGraph();
}

export function autoGenerateFormulaGraph() {
    const tableInput = document.getElementById("grapher-table-dropdown");
    const fieldInput = document.getElementById("grapher-field-dropdown");

    const tableName = tableInput ? tableInput.value.trim() : "";
    const fieldName = fieldInput ? fieldInput.value.trim() : "";

    if (!tableName || !fieldName) {
        return;
    }

    const expandCheckbox = document.getElementById("grapher-expand-fields");
    const depthInput = document.getElementById("grapher-expansion-depth");
    const directionDropdown = document.getElementById("grapher-flowchart-direction");

    const expandFields = !!expandCheckbox?.checked;
    const direction = directionDropdown ? directionDropdown.value : "TD";
    const depthValue = depthInput ? depthInput.value.trim() : "1";
    const maxDepth = depthValue ? parseInt(depthValue, 10) : 1;

    if (typeof window.graphFormulaFromUI !== "undefined") {
        window.graphFormulaFromUI(tableName, fieldName, expandFields, maxDepth, direction);
    }
}

export function downloadFormulaGrapherSVG() {
    const svgElement = document.querySelector("#formula-grapher-mermaid-container .mermaid svg");
    if (!svgElement) return toast.warning("No diagram available to download");
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: "image/svg+xml" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "formula_flowchart.svg";
    link.click();
}

export function openFormulaGrapherInMermaidLive() {
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
    const compressedGraph = pako.deflate(new TextEncoder().encode(JSON.stringify(state)), { level: 9 });
    const encodedGraph = window.Base64.fromUint8Array(compressedGraph, true);
    const mermaidLiveUrl = `https://mermaid.live/edit#pako:${encodedGraph}`;
    window.open(mermaidLiveUrl, "_blank");
}

export function copyFormulaGrapherMermaidText() {
    const graphDefinition = localStorage.getItem("lastFormulaGraphDefinition");
    if (!graphDefinition) return toast.warning("No diagram available to copy");
    navigator.clipboard.writeText(graphDefinition).then(() => {
        toast.success("Mermaid diagram copied to clipboard");
    }).catch((error) => {
        console.error("Error copying to clipboard:", error);
        toast.error("Failed to copy Mermaid diagram to clipboard");
    });
}

export function toggleFormulaGrapherFullscreen() {
    const mermaidContainer = document.getElementById("formula-grapher-mermaid-container");
    if (!document.fullscreenElement) {
        mermaidContainer?.requestFullscreen().catch((err) => {
            toast.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
        });
    } else {
        document.exitFullscreen();
    }
}
