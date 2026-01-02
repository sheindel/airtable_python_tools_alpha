import { getSchema, getTables } from '../components/ui/schema-store.js';
import { getDropdown, setDropdownOptions } from './dom-utils.js';
import { toast } from './toast.js';
import type { DropdownOption, AirtableTable } from '../types/pyscript';
import type { AtDropdownElement } from '../types/dom';

let originalFormulaText: string = "";

/**
 * Update the field dropdown for the compressor tab with formula fields from selected table
 * @param tableId - The ID of the selected table
 */
export function updateCompressorFieldDropdown(tableId: string): void {
    const schemaData = getSchema();
    const fieldDropdown = getDropdown("compressor-field-dropdown");
    const options: DropdownOption[] = [];

    const selectedTable = schemaData?.schema?.tables?.find((table: AirtableTable) => table.id === tableId);
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

    const originalDisplay = document.getElementById("original-formula-display");
    const compressedDisplay = document.getElementById("compressed-formula-display");
    
    if (originalDisplay) {
        originalDisplay.innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">No formula selected</span>';
    }
    if (compressedDisplay) {
        compressedDisplay.innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">Select a formula field to see compressed results</span>';
    }
}

/**
 * Update the original formula display with the selected field's formula
 * @param tableId - The table ID
 * @param fieldId - The field ID
 * @param formula - The formula text
 */
export function updateOriginalFormulaDisplay(_tableId: string, _fieldId: string, formula: string): void {
    originalFormulaText = formula || "";
    const originalDisplay = document.getElementById("original-formula-display");

    if (!originalDisplay) return;

    if (!originalFormulaText) {
        originalDisplay.textContent = "No formula available";
        return;
    }

    const formatSelect = document.getElementById("output-format") as HTMLSelectElement | null;
    const outputFormat = formatSelect ? formatSelect.value as 'field_ids' | 'field_names' : "field_ids";
    updateOriginalFormulaFormat(outputFormat);
    autoCompressFormula();
}

/**
 * Update the original formula display format
 * @param outputFormat - The output format ('field_ids' or 'field_names')
 */
export function updateOriginalFormulaFormat(outputFormat: 'field_ids' | 'field_names'): void {
    const originalDisplay = document.getElementById("original-formula-display");
    if (!originalDisplay || !originalFormulaText) return;

    if (typeof window.convertFormulaDisplay !== "undefined") {
        const convertedFormula = window.convertFormulaDisplay(originalFormulaText, outputFormat);
        const displayFormat = getDisplayFormat();
        const formattedFormula = applyDisplayFormat(convertedFormula, displayFormat);
        originalDisplay.innerHTML = `<span class="text-gray-900 dark:text-gray-100">${formattedFormula.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>`;
    } else {
        originalDisplay.innerHTML = `<span class="text-gray-900 dark:text-gray-100">${originalFormulaText.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>`;
    }
}

/**
 * Handle output format change event
 */
export function onOutputFormatChange(): void {
    const formatSelect = document.getElementById("output-format") as HTMLSelectElement | null;
    if (formatSelect && originalFormulaText) {
        updateOriginalFormulaFormat(formatSelect.value as 'field_ids' | 'field_names');
        autoCompressFormula();
    }
}

/**
 * Handle display format change event
 */
export function onDisplayFormatChange(): void {
    if (originalFormulaText) {
        const formatSelect = document.getElementById("output-format") as HTMLSelectElement | null;
        if (formatSelect) {
            updateOriginalFormulaFormat(formatSelect.value as 'field_ids' | 'field_names');
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

/**
 * Get the current display format
 * @returns The display format ('compact' or 'logical')
 */
export function getDisplayFormat(): 'compact' | 'logical' {
    const displayFormatSelect = document.getElementById("display-format") as HTMLSelectElement | null;
    return displayFormatSelect ? displayFormatSelect.value as 'compact' | 'logical' : "compact";
}

/**
 * Apply display formatting to a formula
 * @param formula - The formula text
 * @param displayFormat - The display format to apply
 * @returns The formatted formula
 */
export function applyDisplayFormat(formula: string, displayFormat: 'compact' | 'logical'): string {
    if (displayFormat === "logical") {
        if (typeof window.formatFormulaLogical !== "undefined") {
            return window.formatFormulaLogical(formula);
        }
    } else if (typeof window.formatFormulaCompact !== "undefined") {
        return window.formatFormulaCompact(formula);
    }
    return formula;
}

/**
 * Compress the selected formula
 */
export function compressFormula(): void {
    const tableInput = document.getElementById("compressor-table-dropdown") as AtDropdownElement | null;
    const fieldInput = document.getElementById("compressor-field-dropdown") as AtDropdownElement | null;
    const depthInput = document.getElementById("compression-depth") as HTMLInputElement | null;
    const formatSelect = document.getElementById("output-format") as HTMLSelectElement | null;
    const displayFormatSelect = document.getElementById("display-format") as HTMLSelectElement | null;

    if (!tableInput || !fieldInput || !formatSelect || !displayFormatSelect) return;

    const tableName = tableInput.value.trim();
    const fieldName = fieldInput.value.trim();

    if (!tableName || !fieldName) {
        toast.warning("Please select both a table and a field.");
        return;
    }

    const depthValue = depthInput?.value.trim() || "";
    const compressionDepth = depthValue ? parseInt(depthValue, 10) : null;
    const outputFormat = formatSelect.value as 'field_ids' | 'field_names';
    const displayFormat = displayFormatSelect.value as 'compact' | 'logical';

    if (typeof window.compressFormulaFromUI !== "undefined") {
        window.compressFormulaFromUI(tableName, fieldName, compressionDepth, outputFormat, displayFormat);
    } else {
        toast.error("Formula compression is not yet initialized. Please refresh the page.");
    }
}

/**
 * Automatically compress formula when parameters change
 */
export function autoCompressFormula(): void {
    const tableInput = document.getElementById("compressor-table-dropdown") as AtDropdownElement | null;
    const fieldInput = document.getElementById("compressor-field-dropdown") as AtDropdownElement | null;

    const tableName = tableInput ? tableInput.value.trim() : "";
    const fieldName = fieldInput ? fieldInput.value.trim() : "";

    if (tableName && fieldName && originalFormulaText) {
        compressFormula();
    }
}

/**
 * Copy compressed formula to clipboard
 */
export function copyCompressedFormula(): void {
    const compressedDisplay = document.getElementById("compressed-formula-display");
    const text = compressedDisplay?.textContent || "";

    if (!text || text.includes("Select a formula field")) {
        toast.warning("No compressed formula to copy");
        return;
    }

    navigator.clipboard.writeText(text).then(() => {
        toast.success("Compressed formula copied to clipboard");
    }).catch((error: Error) => {
        console.error("Error copying to clipboard:", error);
        toast.error("Failed to copy compressed formula to clipboard");
    });
}

/**
 * Generate a CSV report for all formulas in the selected table
 */
export function generateTableReport(): void {
    const tableInput = document.getElementById("compressor-table-dropdown") as AtDropdownElement | null;
    const depthInput = document.getElementById("compression-depth") as HTMLInputElement | null;

    if (!tableInput) return;

    const tableName = tableInput.value.trim();
    if (!tableName) {
        toast.warning("Please select a table.");
        return;
    }

    const depthValue = depthInput?.value.trim() || "";
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
            const errorMessage = error instanceof Error ? error.message : String(error);
            toast.error(`Failed to generate table report: ${errorMessage}`);
        }
    } else {
        toast.error("Table report generation is not yet initialized. Please refresh the page.");
    }
}

/**
 * Initialize the compressor dropdowns with table options
 */
export function initializeCompressorDropdowns(): void {
    const tables = getTables();
    const tableOptions: DropdownOption[] = tables.map((table: AirtableTable) => ({ 
        id: table.id, 
        text: table.name 
    }));
    tableOptions.sort((a, b) => a.text.localeCompare(b.text));
    setDropdownOptions("compressor-table-dropdown", tableOptions);
    setDropdownOptions("compressor-field-dropdown", []);
}
