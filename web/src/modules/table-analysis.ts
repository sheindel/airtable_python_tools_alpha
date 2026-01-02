/**
 * Table Analysis Module
 * Handles the Table Analysis tab logic, including table dependencies analysis,
 * filtering, sorting, and CSV export with PyScript integration.
 */

// Imports available if needed in future
// import { getTables } from "../components/ui/schema-store.js";
// import { setDropdownOptions } from "./dom-utils.js";

// Data format: [source_table, target_table, links, rollups, lookups, total]
type DependencyRow = [string, string, number, number, number, number];

let lastDependenciesData: DependencyRow[] = [];
let filteredDependenciesData: DependencyRow[] = [];
let currentSortColumn: number | null = null;
let currentSortDirection: 'asc' | 'desc' = 'asc';

/**
 * Initialize analysis dropdowns (kept for backward compatibility)
 */
export function initializeAnalysisDropdowns(): void {
    // No longer needed but kept for backward compatibility if called elsewhere
}

/**
 * Generate table dependencies analysis
 */
export function generateTableDependencies(): void {
    if (typeof window.getTableDependencies !== "undefined") {
        try {
            const rawData = window.getTableDependencies();

            if (!rawData || rawData.length === 0) {
                alert("No table dependencies found in this base.");
                return;
            }

            // Convert PyScript proxy objects to native JavaScript arrays using toJs()
            const data: DependencyRow[] = (rawData as any).toJs ? (rawData as any).toJs() : rawData;

            lastDependenciesData = data;
            filteredDependenciesData = [...data];
            currentSortColumn = null;
            currentSortDirection = 'asc';

            // Clear any existing filters
            const sourceFilter = document.getElementById("filter-source-table") as HTMLInputElement | null;
            const targetFilter = document.getElementById("filter-target-table") as HTMLInputElement | null;
            if (sourceFilter) sourceFilter.value = "";
            if (targetFilter) targetFilter.value = "";

            renderDependenciesTable(filteredDependenciesData);

            // Set up filter event listeners
            setupFilterListeners();

            const resultsDiv = document.getElementById("dependencies-results");
            resultsDiv?.classList.remove("hidden");
        } catch (error) {
            console.error("Error generating table dependencies:", error);
            alert(`Failed to generate table dependencies: ${(error as Error).message || error}`);
        }
    } else {
        alert("Table dependencies analysis is not yet initialized. Please refresh the page.");
    }
}

/**
 * Set up filter event listeners
 */
function setupFilterListeners(): void {
    const sourceFilter = document.getElementById("filter-source-table");
    const targetFilter = document.getElementById("filter-target-table");
    const clearButton = document.getElementById("clear-filters-btn");

    if (sourceFilter) {
        sourceFilter.removeEventListener("input", applyFilters);
        sourceFilter.addEventListener("input", applyFilters);
    }

    if (targetFilter) {
        targetFilter.removeEventListener("input", applyFilters);
        targetFilter.addEventListener("input", applyFilters);
    }

    if (clearButton) {
        clearButton.removeEventListener("click", clearFilters);
        clearButton.addEventListener("click", clearFilters);
    }
}

/**
 * Apply filters to the dependencies table
 */
function applyFilters(): void {
    const sourceFilter = (document.getElementById("filter-source-table") as HTMLInputElement)?.value.toLowerCase() || "";
    const targetFilter = (document.getElementById("filter-target-table") as HTMLInputElement)?.value.toLowerCase() || "";

    filteredDependenciesData = lastDependenciesData.filter(row => {
        const matchesSource = row[0].toLowerCase().includes(sourceFilter);
        const matchesTarget = row[1].toLowerCase().includes(targetFilter);
        return matchesSource && matchesTarget;
    });

    renderDependenciesTable(filteredDependenciesData);
}

/**
 * Clear all filters
 */
function clearFilters(): void {
    const sourceFilter = document.getElementById("filter-source-table") as HTMLInputElement | null;
    const targetFilter = document.getElementById("filter-target-table") as HTMLInputElement | null;
    
    if (sourceFilter) sourceFilter.value = "";
    if (targetFilter) targetFilter.value = "";

    filteredDependenciesData = [...lastDependenciesData];
    currentSortColumn = null;
    currentSortDirection = 'asc';
    
    renderDependenciesTable(filteredDependenciesData);
}

/**
 * Sort data by column
 */
function sortData(columnIndex: number): void {
    // Toggle sort direction if clicking the same column
    if (currentSortColumn === columnIndex) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = columnIndex;
        currentSortDirection = 'asc';
    }

    filteredDependenciesData.sort((a, b) => {
        let aVal: string | number = a[columnIndex];
        let bVal: string | number = b[columnIndex];

        // For numeric columns (indices 2-5), compare as numbers
        if (columnIndex >= 2) {
            aVal = Number(aVal);
            bVal = Number(bVal);
        } else {
            // For text columns, case-insensitive comparison
            aVal = String(aVal).toLowerCase();
            bVal = String(bVal).toLowerCase();
        }

        if (aVal < bVal) return currentSortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return currentSortDirection === 'asc' ? 1 : -1;
        return 0;
    });

    renderDependenciesTable(filteredDependenciesData);
}

/**
 * Render the dependencies table
 */
function renderDependenciesTable(data: DependencyRow[]): void {
    // Data format: [source_table, target_table, links, rollups, lookups, total]
    const tableContainer = document.getElementById("dependencies-table-container");
    
    if (!tableContainer) return;

    if (!data || data.length === 0) {
        tableContainer.innerHTML = `
            <div class="p-4 text-center text-gray-500 dark:text-gray-400">
                No dependencies match the current filters.
            </div>
        `;
        return;
    }

    const headers = [
        { label: "Source Table", index: 0 },
        { label: "Target Table", index: 1 },
        { label: "Links", index: 2 },
        { label: "Rollups", index: 3 },
        { label: "Lookups", index: 4 },
        { label: "Total", index: 5 }
    ];

    const html = `
        <div class="overflow-x-auto">
            <table class="min-w-full bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg">
                <thead class="bg-gray-50 dark:bg-gray-600">
                    <tr>
                        ${headers.map(h => `
                            <th class="sortable-header px-4 py-3 ${h.index >= 2 ? 'text-center' : 'text-left'} text-xs font-medium text-gray-700 dark:text-gray-200 uppercase tracking-wider border-b dark:border-gray-500 ${currentSortColumn === h.index ? (currentSortDirection === 'asc' ? 'sorted-asc' : 'sorted-desc') : ''}" 
                                data-column="${h.index}">
                                ${h.label}
                                <span class="sort-indicator"></span>
                            </th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-600">
                    ${data
                        .map(
                            (row, idx) => `
                        <tr class="${idx % 2 === 0 ? "bg-white dark:bg-gray-700" : "bg-gray-50 dark:bg-gray-800"}">
                            <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">${row[0]}</td>
                            <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">${row[1]}</td>
                            <td class="px-4 py-3 text-sm text-center text-gray-700 dark:text-gray-300">${row[2]}</td>
                            <td class="px-4 py-3 text-sm text-center text-gray-700 dark:text-gray-300">${row[3]}</td>
                            <td class="px-4 py-3 text-sm text-center text-gray-700 dark:text-gray-300">${row[4]}</td>
                            <td class="px-4 py-3 text-sm text-center font-semibold text-gray-900 dark:text-gray-100">${row[5]}</td>
                        </tr>
                    `
                        )
                        .join("")}
                </tbody>
            </table>
        </div>
    `;

    tableContainer.innerHTML = html;

    // Add click listeners to sortable headers
    const sortableHeaders = tableContainer.querySelectorAll('.sortable-header');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const columnIndex = parseInt((header as HTMLElement).dataset.column || "0");
            sortData(columnIndex);
        });
    });
}

/**
 * Download table dependencies as CSV
 */
export function downloadTableDependenciesCSV(): void {
    if (!lastDependenciesData || lastDependenciesData.length === 0) {
        alert("No data to download");
        return;
    }

    // Data format: [source_table, target_table, links, rollups, lookups, total]
    const headers = ["Source Table", "Target Table", "Links", "Rollups", "Lookups", "Total"];
    const csvContent = [headers, ...lastDependenciesData].map((row) => row.join(",")).join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    const filename = "table_dependencies.csv";

    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
