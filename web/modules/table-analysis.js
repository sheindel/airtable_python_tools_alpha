import { getTables } from "../components/ui/schema-store.js";
import { setDropdownOptions } from "./dom-utils.js";

let lastAnalysisCSV = [];

export function initializeAnalysisDropdowns() {
    const tables = getTables();
    const options = tables.map((table) => ({ id: table.id, text: table.name }));
    options.sort((a, b) => a.text.localeCompare(b.text));
    setDropdownOptions("analysis-table-dropdown", options);
}

export function generateTableComplexityCSV() {
    const tableInput = document.getElementById("analysis-table-dropdown");
    const tableName = tableInput?.value.trim() || "";

    if (!tableName) {
        alert("Please select a table.");
        return;
    }

    if (typeof window.getTableComplexityData !== "undefined") {
        try {
            const csvData = window.getTableComplexityData(tableName);

            if (!csvData || csvData.length === 0) {
                alert("No complexity data found for this table.");
                return;
            }

            lastAnalysisCSV = csvData;

            const csvOutput = document.getElementById("analysis-csv-output");
            const resultsDiv = document.getElementById("analysis-results");

            const csvString = csvData.map((row) => row.join(",")).join("\n");
            if (csvOutput) {
                csvOutput.textContent = csvString;
            }

            resultsDiv?.classList.remove("hidden");
        } catch (error) {
            console.error("Error generating table complexity:", error);
            alert(`Failed to generate table complexity: ${error.message || error}`);
        }
    } else {
        alert("Table complexity analysis is not yet initialized. Please refresh the page.");
    }
}

export function downloadTableComplexityCSV() {
    if (!lastAnalysisCSV || lastAnalysisCSV.length === 0) {
        alert("No data to download");
        return;
    }

    const tableInput = document.getElementById("analysis-table-dropdown");
    const tableName = tableInput?.value.trim() || "table";
    const csvString = lastAnalysisCSV.map((row) => row.join(",")).join("\n");

    const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    const filename = `${tableName}_field_complexity.csv`;

    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
