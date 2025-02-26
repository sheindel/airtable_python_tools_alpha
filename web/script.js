document.addEventListener("DOMContentLoaded", () => {
    updateSchemaInfo();
    document.getElementById("table-dropdown").addEventListener("change", updateFieldDropdown);
    // document.getElementById("field-dropdown").addEventListener("change", function() {
    //     const selectedField = this.options[this.selectedIndex].text;
    //     updateMermaidDiagram(selectedField);
    // });
});

async function fetchSchema() {
    const baseId = document.getElementById("base-id").value;
    const pat = document.getElementById("pat").value;
    if (!baseId || !pat) {
        alert("Please enter both Base ID and PAT.");
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
        const timestamp = new Date().toISOString();
        localStorage.setItem("airtableSchema", JSON.stringify({ schema, timestamp }));
        updateSchemaInfo();
    } catch (error) {
        console.error("Error fetching schema:", error);
        alert("Failed to retrieve schema.");
    }
}

function updateSchemaInfo() {
    const schemaData = JSON.parse(localStorage.getItem("airtableSchema"));
    document.getElementById("last-refresh").textContent = schemaData ? `Last Refresh: ${schemaData.timestamp}` : "Last Refresh: Not yet retrieved";

    const tableDropdown = document.getElementById("table-dropdown");
    tableDropdown.innerHTML = "";

    if (schemaData?.schema?.tables) {
        schemaData.schema.tables.forEach(table => {
            const option = document.createElement("option");
            option.value = table.id;
            option.textContent = table.name;
            tableDropdown.appendChild(option);
        });

        // Automatically update the field dropdown for the first table
        if (schemaData.schema.tables.length > 0) {
            tableDropdown.value = schemaData.schema.tables[0].id;
            updateFieldDropdown();
        }
    }
}

function updateFieldDropdown() {
    const schemaData = JSON.parse(localStorage.getItem("airtableSchema"));
    const tableDropdown = document.getElementById("table-dropdown");
    const fieldDropdown = document.getElementById("field-dropdown");
    const selectedTableId = tableDropdown.value;

    fieldDropdown.innerHTML = "";

    if (schemaData?.schema?.tables) {
        const selectedTable = schemaData.schema.tables.find(table => table.id === selectedTableId);
        selectedTable?.fields.forEach(field => {
            const option = document.createElement("option");
            option.value = field.id;
            option.textContent = field.name;
            fieldDropdown.appendChild(option);
        });

        // Automatically update the Mermaid diagram for the first field
        if (selectedTable.fields.length > 0) {
            fieldDropdown.value = selectedTable.fields[0].id;
        }
    }
}

function downloadMermaidSVG() {
    const svgElement = document.querySelector(".mermaid svg");
    if (!svgElement) return alert("No diagram available to download");
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: "image/svg+xml" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "diagram.svg";
    link.click();
}

function openInMermaidLive() {
    const graphDefinition = document.querySelector(".mermaid").textContent;
    const compressedGraph = pako.deflate(new TextEncoder().encode(graphDefinition), { level: 9 });
    const encodedGraph = window.Base64.fromUint8Array(compressedGraph, true);
    const mermaidLiveUrl = `https://mermaid.live/edit#pako:${encodedGraph}`;
    window.open(mermaidLiveUrl, "_blank");
}

function toggleFullscreen() {
    const mermaidContainer = document.getElementById("mermaid-container");
    if (!document.fullscreenElement) {
        mermaidContainer?.requestFullscreen().catch(err => {
            alert(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
        });
    } else {
        document.exitFullscreen();
    }
}

function downloadMermaidText() {
    const graphDefinition = localStorage.getItem("lastGraphDefinition");
    if (!graphDefinition) return alert("No diagram available to download");
    const blob = new Blob([graphDefinition], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "diagram.mmd";
    link.click();
}

window.fetchSchema = fetchSchema;
window.downloadMermaidSVG = downloadMermaidSVG;
window.openInMermaidLive = openInMermaidLive;
window.toggleFullscreen = toggleFullscreen;
window.downloadMermaidText = downloadMermaidText;