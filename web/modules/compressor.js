import { getSchema, getTables } from "../components/ui/schema-store.js";
import { getDropdown, setDropdownOptions } from "./dom-utils.js";
import { toast } from "./toast.js";

let originalFormulaText = "";

export function updateCompressorFieldDropdown(tableId) {
    const schemaData = getSchema();
    const fieldDropdown = getDropdown("compressor-field-dropdown");
    const options = [];

    const selectedTable = schemaData?.schema?.tables?.find((table) => table.id === tableId);
    selectedTable?.fields.forEach((field) => {
        if (field.type === "formula") {
            options.push({
                id: field.id,
                text: field.name,
                tableId,
                formula: field.options?.formula || "",
            });
        }
    });

    options.sort((a, b) => a.text.localeCompare(b.text));
    if (fieldDropdown) {
        fieldDropdown.value = "";
    }
    setDropdownOptions("compressor-field-dropdown", options);

    document.getElementById("original-formula-display").innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">No formula selected</span>';
    document.getElementById("compressed-formula-display").innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">Select a formula field to see compressed results</span>';
}

export function updateOriginalFormulaDisplay(tableId, fieldId, formula) {
    originalFormulaText = formula || "";
    const originalDisplay = document.getElementById("original-formula-display");

    if (!originalFormulaText) {
        originalDisplay.textContent = "No formula available";
        return;
    }

    const formatSelect = document.getElementById("output-format");
    const outputFormat = formatSelect ? formatSelect.value : "field_ids";
    updateOriginalFormulaFormat(outputFormat);
    autoCompressFormula();
}

export function updateOriginalFormulaFormat(outputFormat) {
    const originalDisplay = document.getElementById("original-formula-display");
    if (!originalFormulaText) return;

    if (typeof window.convertFormulaDisplay !== "undefined") {
        const convertedFormula = window.convertFormulaDisplay(originalFormulaText, outputFormat);
        const displayFormat = getDisplayFormat();
        const formattedFormula = applyDisplayFormat(convertedFormula, displayFormat);
        originalDisplay.innerHTML = `<span class="text-gray-900 dark:text-gray-100">${formattedFormula.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>`;
    } else {
        originalDisplay.innerHTML = `<span class="text-gray-900 dark:text-gray-100">${originalFormulaText.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>`;
    }
}

export function onOutputFormatChange() {
    const formatSelect = document.getElementById("output-format");
    if (formatSelect && originalFormulaText) {
        updateOriginalFormulaFormat(formatSelect.value);
        autoCompressFormula();
    }
}

export function onDisplayFormatChange() {
    if (originalFormulaText) {
        const formatSelect = document.getElementById("output-format");
        if (formatSelect) {
            updateOriginalFormulaFormat(formatSelect.value);
        }
    }

    const compressedDisplay = document.getElementById("compressed-formula-display");
    if (compressedDisplay && compressedDisplay.textContent && !compressedDisplay.textContent.includes("Select a formula field")) {
        const rawText = compressedDisplay.getAttribute("data-raw-formula");
        if (rawText) {
            const displayFormat = getDisplayFormat();
            const formattedFormula = applyDisplayFormat(rawText, displayFormat);
            compressedDisplay.innerHTML = `<span class="text-gray-900 dark:text-gray-100">${formattedFormula.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>`;
        }
    }
}

export function getDisplayFormat() {
    const displayFormatSelect = document.getElementById("display-format");
    return displayFormatSelect ? displayFormatSelect.value : "compact";
}

export function applyDisplayFormat(formula, displayFormat) {
    if (displayFormat === "logical") {
        if (typeof window.formatFormulaLogical !== "undefined") {
            return window.formatFormulaLogical(formula);
        }
    } else if (typeof window.formatFormulaCompact !== "undefined") {
        return window.formatFormulaCompact(formula);
    }
    return formula;
}

export function compressFormula() {
    const tableInput = document.getElementById("compressor-table-dropdown");
    const fieldInput = document.getElementById("compressor-field-dropdown");
    const depthInput = document.getElementById("compression-depth");
    const formatSelect = document.getElementById("output-format");
    const displayFormatSelect = document.getElementById("display-format");

    const tableName = tableInput.value.trim();
    const fieldName = fieldInput.value.trim();

    if (!tableName || !fieldName) {
        toast.warning("Please select both a table and a field.");
        return;
    }

    const depthValue = depthInput.value.trim();
    const compressionDepth = depthValue ? parseInt(depthValue, 10) : null;
    const outputFormat = formatSelect.value;
    const displayFormat = displayFormatSelect.value;

    if (typeof window.compressFormulaFromUI !== "undefined") {
        window.compressFormulaFromUI(tableName, fieldName, compressionDepth, outputFormat, displayFormat);
    } else {
        toast.error("Formula compression is not yet initialized. Please refresh the page.");
    }
}

export function autoCompressFormula() {
    const tableInput = document.getElementById("compressor-table-dropdown");
    const fieldInput = document.getElementById("compressor-field-dropdown");

    const tableName = tableInput ? tableInput.value.trim() : "";
    const fieldName = fieldInput ? fieldInput.value.trim() : "";

    if (tableName && fieldName && originalFormulaText) {
        compressFormula();
    }
}

export function copyCompressedFormula() {
    const compressedDisplay = document.getElementById("compressed-formula-display");
    const text = compressedDisplay?.textContent || "";

    if (!text || text.includes("Select a formula field")) {
        toast.warning("No compressed formula to copy");
        return;
    }

    navigator.clipboard.writeText(text).then(() => {
        toast.success("Compressed formula copied to clipboard");
    }).catch((error) => {
        console.error("Error copying to clipboard:", error);
        toast.error("Failed to copy compressed formula to clipboard");
    });
}

export function generateTableReport() {
    const tableInput = document.getElementById("compressor-table-dropdown");
    const depthInput = document.getElementById("compression-depth");

    const tableName = tableInput.value.trim();
    if (!tableName) {
        toast.warning("Please select a table.");
        return;
    }

    const depthValue = depthInput.value.trim();
    const compressionDepth = depthValue ? parseInt(depthValue, 10) : null;

    if (typeof window.generateTableReportData !== "undefined") {
        try {
            const csvData = window.generateTableReportData(tableName, compressionDepth);
            const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);
            const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
            const filename = `${tableName}_formula_report_${timestamp}.csv`;

            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            toast.success(`Table report generated successfully for "${tableName}"!`);
        } catch (error) {
            console.error("Error generating table report:", error);
            toast.error(`Failed to generate table report: ${error.message || error}`);
        }
    } else {
        toast.error("Table report generation is not yet initialized. Please refresh the page.");
    }
}

export function initializeCompressorDropdowns() {
    const tables = getTables();
    const tableOptions = tables.map((table) => ({ id: table.id, text: table.name }));
    tableOptions.sort((a, b) => a.text.localeCompare(b.text));
    setDropdownOptions("compressor-table-dropdown", tableOptions);
    setDropdownOptions("compressor-field-dropdown", []);
}
