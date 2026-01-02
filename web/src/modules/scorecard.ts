/**
 * Complexity Scorecard Module
 * Handles the Complexity Scorecard tab logic, including field analysis,
 * sorting, filtering, and CSV export with PyScript integration.
 */

import { getSchema } from "../components/ui/schema-store.js";
import { escapeHtml } from "./dom-utils.js";

interface ScorecardField {
    complexity_score: number;
    table_name: string;
    field_name: string;
    field_type: string;
    max_depth: number;
    backward_deps: number;
    forward_deps: number;
    cross_table_deps: number;
}

interface ComplexitySummary {
    total_computed_fields: number;
    avg_complexity_score: number;
    max_complexity_score: number;
}

type SortField = keyof ScorecardField;

let scorecardData: ScorecardField[] = [];
let scorecardSortField: SortField = "complexity_score";
let scorecardSortAsc = false;

/**
 * Initialize the scorecard table filter dropdown
 */
export function initializeScorecardDropdowns(): void {
    const tableFilter = document.getElementById("scorecard-table-filter") as HTMLSelectElement | null;
    if (!tableFilter) return;

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

/**
 * Refresh the complexity scorecard with current filters
 */
export function refreshComplexityScorecard(): void {
    const tableFilter = document.getElementById("scorecard-table-filter") as HTMLSelectElement | null;
    const minScoreInput = document.getElementById("scorecard-min-score") as HTMLInputElement | null;

    const filterTable = tableFilter ? tableFilter.value : "";
    const minScore = minScoreInput ? parseFloat(minScoreInput.value) || 0 : 0;

    initializeScorecardDropdowns();

    const tbody = document.getElementById("scorecard-table-body");
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400 italic">
                    <div class="flex items-center justify-center">
                        <svg class="animate-spin h-5 w-5 mr-3 text-blue-500" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing complexity... This may take a moment for large bases.
                    </div>
                </td>
            </tr>
        `;
    }

    setTimeout(() => {
        if (typeof window.getComplexityScorecardData !== "undefined") {
            try {
                const jsonData = window.getComplexityScorecardData(filterTable || null, minScore);
                scorecardData = JSON.parse(jsonData) as ScorecardField[];

                updateComplexitySummary();
                renderScorecardTable();
            } catch (error) {
                console.error("Error getting complexity data:", error);
                if (tbody) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="8" class="px-4 py-8 text-center text-red-500 dark:text-red-400">
                                Failed to get complexity data. Make sure you have loaded a schema.
                            </td>
                        </tr>
                    `;
                }
            }
        } else {
            alert("Complexity scorecard is not yet initialized. Please refresh the page.");
        }
    }, 50);
}

/**
 * Sort the scorecard table by a field
 */
export function sortScorecardBy(field: SortField): void {
    if (scorecardSortField === field) {
        scorecardSortAsc = !scorecardSortAsc;
    } else {
        scorecardSortField = field;
        scorecardSortAsc = field === "table_name" || field === "field_name";
    }

    renderScorecardTable();
}

/**
 * Download the complexity scorecard as CSV
 */
export function downloadComplexityCSV(): void {
    if (typeof window.exportComplexityCSV !== "undefined") {
        try {
            const csvData = window.exportComplexityCSV();
            const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);

            const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
            const filename = `complexity_scorecard_${timestamp}.csv`;

            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error("Error exporting CSV:", error);
            alert("Failed to export CSV");
        }
    } else {
        alert("Export function not available. Please refresh the page.");
    }
}

/**
 * Update the complexity summary statistics
 */
function updateComplexitySummary(): void {
    if (typeof window.getComplexitySummary !== "undefined") {
        try {
            const jsonData = window.getComplexitySummary();
            const summary = JSON.parse(jsonData) as ComplexitySummary;

            const totalEl = document.getElementById("summary-total-fields");
            const avgEl = document.getElementById("summary-avg-score");
            const maxEl = document.getElementById("summary-max-score");
            const highEl = document.getElementById("summary-high-count");

            if (totalEl) totalEl.textContent = String(summary.total_computed_fields || 0);
            if (avgEl) avgEl.textContent = String(summary.avg_complexity_score || 0);
            if (maxEl) maxEl.textContent = String(summary.max_complexity_score || 0);

            const highCount = scorecardData.filter((f) => f.complexity_score > 20).length;
            if (highEl) highEl.textContent = String(highCount);
        } catch (error) {
            console.error("Error getting summary:", error);
        }
    }
}

/**
 * Render the scorecard table with current data and sorting
 */
function renderScorecardTable(): void {
    const tbody = document.getElementById("scorecard-table-body");
    if (!tbody) return;

    if (!scorecardData || scorecardData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400 italic">
                    No computed fields found. Make sure you have loaded a schema.
                </td>
            </tr>
        `;
        return;
    }

    const sortedData = [...scorecardData].sort((a, b) => {
        let aVal: string | number = a[scorecardSortField];
        let bVal: string | number = b[scorecardSortField];

        if (typeof aVal === "string") {
            aVal = aVal.toLowerCase();
            bVal = (bVal as string).toLowerCase();
            return scorecardSortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        }

        return scorecardSortAsc ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
    });

    const rows = sortedData.map((field) => {
        const scoreClass = getScoreColorClass(field.complexity_score);
        const typeIcon = getFieldTypeIcon(field.field_type);

        return `
            <tr class="bg-white dark:bg-gray-800 border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3">
                    <span class="px-2 py-1 rounded text-sm font-medium ${scoreClass}">
                        ${field.complexity_score}
                    </span>
                </td>
                <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">
                    ${escapeHtml(field.table_name)}
                </td>
                <td class="px-4 py-3 text-gray-700 dark:text-gray-300">
                    ${escapeHtml(field.field_name)}
                </td>
                <td class="px-4 py-3">
                    <span class="text-lg" title="${field.field_type}">${typeIcon}</span>
                </td>
                <td class="px-4 py-3 text-center">${field.max_depth}</td>
                <td class="px-4 py-3 text-center">${field.backward_deps}</td>
                <td class="px-4 py-3 text-center">${field.forward_deps}</td>
                <td class="px-4 py-3 text-center">
                    ${field.cross_table_deps > 1 ?
                        `<span class="text-orange-600 dark:text-orange-400 font-medium">${field.cross_table_deps}</span>` :
                        field.cross_table_deps}
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = rows.join("");
}

/**
 * Get the CSS class for a complexity score badge
 */
function getScoreColorClass(score: number): string {
    if (score >= 50) return "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300";
    if (score >= 30) return "bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-300";
    if (score >= 20) return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-300";
    if (score >= 10) return "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300";
    return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300";
}

/**
 * Get the icon for a field type
 */
function getFieldTypeIcon(fieldType: string): string {
    const icons: Record<string, string> = {
        formula: "f<sub>x</sub>",
        rollup: "🧻",
        multipleLookupValues: "🔭",
        count: "🗳️",
    };
    return icons[fieldType] || "📊";
}
