import { getSchema } from "../components/ui/schema-store.js";
import { escapeHtml } from "./dom-utils.js";
import { toast } from "./toast.js";

let unusedFieldsData = [];
let unusedSortField = "table_name";
let unusedSortAsc = true;

export function initializeUnusedDropdowns() {
    const tableFilter = document.getElementById("unused-table-filter");
    const typeFilter = document.getElementById("unused-type-filter");

    if (tableFilter) {
        tableFilter.innerHTML = '<option value="">All Tables</option>';
        const schemaData = getSchema();
        const tableNames = schemaData?.schema?.tables?.map((t) => t.name).sort() || [];
        tableNames.forEach((name) => {
            const option = document.createElement("option");
            option.value = name;
            option.textContent = name;
            tableFilter.appendChild(option);
        });
    }

    if (typeFilter) {
        typeFilter.innerHTML = '<option value="">All Types</option>';
        if (typeof window.getFieldTypesForDropdown !== "undefined") {
            try {
                const types = window.getFieldTypesForDropdown();
                types.forEach((type) => {
                    const option = document.createElement("option");
                    option.value = type;
                    option.textContent = type;
                    typeFilter.appendChild(option);
                });
            } catch (error) {
                console.error("Error getting field types:", error);
            }
        }
    }
}

export function refreshUnusedFields() {
    const tableFilter = document.getElementById("unused-table-filter");
    const typeFilter = document.getElementById("unused-type-filter");

    const filterTable = tableFilter ? tableFilter.value : "";
    const filterType = typeFilter ? typeFilter.value : "";

    initializeUnusedDropdowns();

    if (typeof window.getUnusedFieldsData !== "undefined") {
        try {
            const jsonData = window.getUnusedFieldsData(filterTable, filterType);
            unusedFieldsData = JSON.parse(jsonData);

            updateUnusedSummary();
            renderUnusedTable();
        } catch (error) {
            console.error("Error getting unused fields data:", error);
            console.error("Error details:", error.message, error.stack);
            toast.error(`Failed to get unused fields data. Make sure you have loaded a schema. Error: ${error.message || error}`);
        }
    } else {
        toast.error("Unused fields detector is not yet initialized. Please refresh the page.");
    }
}

export function sortUnusedBy(field) {
    if (unusedSortField === field) {
        unusedSortAsc = !unusedSortAsc;
    } else {
        unusedSortField = field;
        unusedSortAsc = true;
    }

    renderUnusedTable();
}

export function downloadUnusedFieldsCSV() {
    if (typeof window.exportUnusedFieldsCSV !== "undefined") {
        try {
            const csvData = window.exportUnusedFieldsCSV();

            const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);

            const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
            const filename = `unused_fields_${timestamp}.csv`;

            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error("Error exporting CSV:", error);
            toast.error("Failed to export CSV");
        }
    } else {
        toast.error("Export function not available. Please refresh the page.");
    }
}

function updateUnusedSummary() {
    if (typeof window.getUnusedFieldsSummary !== "undefined") {
        try {
            const jsonData = window.getUnusedFieldsSummary();
            const summary = JSON.parse(jsonData);

            const totalEl = document.getElementById("unused-summary-total");
            const countEl = document.getElementById("unused-summary-count");
            const percentEl = document.getElementById("unused-summary-percent");
            const tablesEl = document.getElementById("unused-summary-tables");

            if (totalEl) totalEl.textContent = summary.total_fields || 0;
            if (countEl) countEl.textContent = summary.unused_count || 0;
            if (percentEl) percentEl.textContent = `${summary.unused_percentage || 0}%`;
            if (tablesEl) tablesEl.textContent = `${summary.tables_with_unused || 0}/${summary.total_tables || 0}`;
        } catch (error) {
            console.error("Error getting unused summary:", error);
        }
    }
}

function renderUnusedTable() {
    const tbody = document.getElementById("unused-table-body");
    if (!tbody) return;

    if (!unusedFieldsData || unusedFieldsData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400 italic">
                    No unused fields found — all fields are referenced somewhere!
                </td>
            </tr>
        `;
        return;
    }

    const sortedData = [...unusedFieldsData].sort((a, b) => {
        let aVal = a[unusedSortField];
        let bVal = b[unusedSortField];

        if (typeof aVal === "string") {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
            return unusedSortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        }

        return unusedSortAsc ? aVal - bVal : bVal - aVal;
    });

    const rows = sortedData.map((field) => {
        const typeIcon = getFieldTypeIconUnused(field.field_type);

        return `
            <tr class="bg-white dark:bg-gray-800 border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">
                    ${escapeHtml(field.table_name)}
                </td>
                <td class="px-4 py-3 text-gray-700 dark:text-gray-300">
                    ${escapeHtml(field.field_name)}
                </td>
                <td class="px-4 py-3">
                    <span class="text-lg" title="${field.field_type}">${typeIcon}</span>
                    <span class="text-xs text-gray-500 dark:text-gray-400 ml-1">${field.field_type}</span>
                </td>
                <td class="px-4 py-3 text-center">
                    ${field.outbound_count > 0 ?
                        `<span class="text-blue-600 dark:text-blue-400">${field.outbound_count}</span>` :
                        '<span class="text-gray-400">0</span>'}
                </td>
                <td class="px-4 py-3">
                    <span class="px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300">
                        Not Referenced
                    </span>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = rows.join("");
}

function getFieldTypeIconUnused(fieldType) {
    const icons = {
        formula: "f<sub>x</sub>",
        rollup: "🧻",
        multipleLookupValues: "🔭",
        count: "🗳️",
        multipleRecordLinks: "🔗",
        singleSelect: "→",
        multipleSelects: "☰",
        singleLineText: "📝",
        multilineText: "📝",
        richText: "📝",
        number: "🔢",
        checkbox: "☑️",
        date: "📅",
        createdTime: "🕒",
        lastModifiedTime: "🕒",
        email: "📧",
        url: "🔗",
        percent: "📊",
        rating: "⭐",
        duration: "⏱️",
        multipleAttachments: "📎",
        autoNumber: "↓",
    };
    return icons[fieldType] || "📊";
}
