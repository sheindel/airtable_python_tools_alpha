document.addEventListener("DOMContentLoaded", () => {
    // Initialize dark mode
    initializeDarkMode();
    
    updateSchemaInfo();
    document.getElementById("table-dropdown").addEventListener("change", updateFieldDropdown);
    
    // Close dropdowns when clicking outside
    document.addEventListener("click", (event) => {
        const tableDropdown = document.getElementById("table-dropdown");
        const tableList = document.getElementById("table-dropdown-list");
        const fieldDropdown = document.getElementById("field-dropdown");
        const fieldList = document.getElementById("field-dropdown-list");
        const compressorTableDropdown = document.getElementById("compressor-table-dropdown");
        const compressorTableList = document.getElementById("compressor-table-dropdown-list");
        const compressorFieldDropdown = document.getElementById("compressor-field-dropdown");
        const compressorFieldList = document.getElementById("compressor-field-dropdown-list");
        const analysisTableDropdown = document.getElementById("analysis-table-dropdown");
        const analysisTableList = document.getElementById("analysis-table-dropdown-list");
        
        // Close table dropdown if click is outside
        if (!tableDropdown.contains(event.target) && !tableList.contains(event.target)) {
            tableList.classList.add("hidden");
        }
        
        // Close field dropdown if click is outside
        if (!fieldDropdown.contains(event.target) && !fieldList.contains(event.target)) {
            fieldList.classList.add("hidden");
        }
        
        // Close compressor table dropdown if click is outside
        if (compressorTableDropdown && compressorTableList && 
            !compressorTableDropdown.contains(event.target) && 
            !compressorTableList.contains(event.target)) {
            compressorTableList.classList.add("hidden");
        }
        
        // Close compressor field dropdown if click is outside
        if (compressorFieldDropdown && compressorFieldList && 
            !compressorFieldDropdown.contains(event.target) && 
            !compressorFieldList.contains(event.target)) {
            compressorFieldList.classList.add("hidden");
        }
        
        // Close analysis table dropdown if click is outside
        if (analysisTableDropdown && analysisTableList && 
            !analysisTableDropdown.contains(event.target) && 
            !analysisTableList.contains(event.target)) {
            analysisTableList.classList.add("hidden");
        }
        
        // Close grapher table dropdown if click is outside
        const grapherTableDropdown = document.getElementById("grapher-table-dropdown");
        const grapherTableList = document.getElementById("grapher-table-dropdown-list");
        const grapherFieldDropdown = document.getElementById("grapher-field-dropdown");
        const grapherFieldList = document.getElementById("grapher-field-dropdown-list");
        
        if (grapherTableDropdown && grapherTableList && 
            !grapherTableDropdown.contains(event.target) && 
            !grapherTableList.contains(event.target)) {
            grapherTableList.classList.add("hidden");
        }
        
        // Close grapher field dropdown if click is outside
        if (grapherFieldDropdown && grapherFieldList && 
            !grapherFieldDropdown.contains(event.target) && 
            !grapherFieldList.contains(event.target)) {
            grapherFieldList.classList.add("hidden");
        }
    });
});

// Wait for PyScript to be ready before calling Python functions
addEventListener('py:ready', () => {
    console.log('PyScript is ready - tabs initialized');
    
    // Add event listener for output format changes
    const outputFormatSelect = document.getElementById("output-format");
    if (outputFormatSelect) {
        outputFormatSelect.addEventListener("change", onOutputFormatChange);
    }
    
    // Add event listener for display format changes
    const displayFormatSelect = document.getElementById("display-format");
    if (displayFormatSelect) {
        displayFormatSelect.addEventListener("change", onDisplayFormatChange);
    }
});

let tableOptions = [];
let fieldOptions = [];
let compressorTableOptions = [];
let compressorFieldOptions = [];
let analysisTableOptions = [];
let grapherTableOptions = [];
let grapherFieldOptions = [];
let originalFormulaText = ""; // Store original formula with field IDs
let lastAnalysisCSV = ""; // Store CSV data for download

// Dark mode functionality
function initializeDarkMode() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
    
    // Check if user has a saved preference, otherwise use system preference
    const savedTheme = localStorage.getItem('color-theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        document.documentElement.classList.add('dark');
        themeToggleLightIcon.classList.remove('hidden');
    } else {
        document.documentElement.classList.remove('dark');
        themeToggleDarkIcon.classList.remove('hidden');
    }
    
    // Toggle dark mode
    themeToggleBtn.addEventListener('click', () => {
        // Toggle icons
        themeToggleDarkIcon.classList.toggle('hidden');
        themeToggleLightIcon.classList.toggle('hidden');
        
        // Toggle dark class on html element
        if (document.documentElement.classList.contains('dark')) {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('color-theme', 'light');
        } else {
            document.documentElement.classList.add('dark');
            localStorage.setItem('color-theme', 'dark');
        }
    });
}


// Tab switching functionality
function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Update tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        if (button.getAttribute('data-tab') === tabName) {
            button.classList.add('active', 'border-blue-500', 'text-blue-600');
            button.classList.remove('border-transparent', 'text-gray-500');
            // Add dark mode class for active state
            button.classList.add('dark:text-blue-400', 'dark:border-blue-400');
            button.classList.remove('dark:text-gray-400');
        } else {
            button.classList.remove('active', 'border-blue-500', 'text-blue-600', 'dark:text-blue-400', 'dark:border-blue-400');
            button.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-400');
        }
    });
    
    // Update tab content visibility
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        if (content.id === `${tabName}-tab`) {
            content.classList.remove('hidden');
            content.classList.add('active');
        } else {
            content.classList.add('hidden');
            content.classList.remove('active');
        }
    });
    
    // Call Python tab switching handler if available
    if (typeof switchTabPython !== 'undefined') {
        switchTabPython(tabName);
    }
}

function filterTableDropdown() {
    const input = document.getElementById("table-dropdown");
    const list = document.getElementById("table-dropdown-list");
    const filter = input.value.toLowerCase();
    list.innerHTML = "";
    list.classList.remove("hidden");

    const filteredOptions = tableOptions.filter(option =>
        option.text.toLowerCase().includes(filter)
    );

    filteredOptions.forEach(option => {
        const div = document.createElement("div");
        div.classList.add("p-2", "cursor-pointer", "hover:bg-gray-200", "dark:hover:bg-gray-600", "dark:text-white");
        div.textContent = option.text;
        div.onclick = () => {
            input.value = option.text;
            list.classList.add("hidden");
            updateFieldDropdown(option.id);
        };
        list.appendChild(div);
    });

    if (filteredOptions.length === 0) {
        const noResultsDiv = document.createElement("div");
        noResultsDiv.classList.add("p-2", "text-gray-500", "dark:text-gray-400");
        noResultsDiv.textContent = "No tables found";
        list.appendChild(noResultsDiv);
    }
}

function filterFieldDropdown() {
    const input = document.getElementById("field-dropdown");
    const list = document.getElementById("field-dropdown-list");
    const filter = input.value.toLowerCase();
    list.innerHTML = "";
    list.classList.remove("hidden");

    const filteredOptions = fieldOptions.filter(option =>
        option.text.toLowerCase().includes(filter)
    );

    filteredOptions.forEach(option => {
        const div = document.createElement("div");
        div.classList.add("p-2", "cursor-pointer", "hover:bg-gray-200", "dark:hover:bg-gray-600", "dark:text-white");
        // Style the special option differently
        if (option.id === "__TABLE_DEPENDENCIES__") {
            div.classList.add("font-semibold", "text-blue-600", "dark:text-blue-400");
        }
        div.textContent = option.text;
        div.onclick = () => {
            input.value = option.text;
            list.classList.add("hidden");
            if (typeof updateMermaidGraph !== 'undefined') {
                updateMermaidGraph(option.tableId, option.id, document.getElementById("flowchart-type").value);
            }
        };
        list.appendChild(div);
    });

    if (filteredOptions.length === 0) {
        const noResultsDiv = document.createElement("div");
        noResultsDiv.classList.add("p-2", "text-gray-500", "dark:text-gray-400");
        noResultsDiv.textContent = "No fields found";
        list.appendChild(noResultsDiv);
    }
}

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

    tableOptions = [];

    if (schemaData?.schema?.tables) {
        schemaData.schema.tables.forEach(table => {
            const option = {
                id: table.id,
                text: table.name
            };
            tableOptions.push(option);
        });
        
        // Sort tables alphabetically
        tableOptions.sort((a, b) => a.text.localeCompare(b.text));
        
        // Populate dropdown with sorted options
        tableOptions.forEach(option => {
            const div = document.createElement("div");
            div.textContent = option.text;
            div.onclick = () => {
                tableDropdown.value = option.text;
                document.getElementById("table-dropdown-list").classList.add("hidden");
                updateFieldDropdown(option.id);
            };
            document.getElementById("table-dropdown-list").appendChild(div);
        });
    }
    
    // Initialize compressor dropdowns
    initializeCompressorDropdowns();
}

function updateFieldDropdown(tableId) {
    const schemaData = JSON.parse(localStorage.getItem("airtableSchema"));
    const fieldDropdown = document.getElementById("field-dropdown");
    
    // Clear the field input value
    fieldDropdown.value = "";
    
    fieldOptions = [];

    // Add special option for table dependencies
    fieldOptions.push({
        id: "__TABLE_DEPENDENCIES__",
        text: "<Show Table Dependencies>",
        tableId: tableId
    });

    if (schemaData?.schema?.tables) {
        const selectedTable = schemaData.schema.tables.find(table => table.id === tableId);
        selectedTable?.fields.forEach(field => {
            const option = {
                id: field.id,
                text: field.name,
                tableId: tableId
            };
            fieldOptions.push(option);
        });
        
        // Sort fields alphabetically (but keep the special option first)
        const specialOption = fieldOptions.shift();
        fieldOptions.sort((a, b) => a.text.localeCompare(b.text));
        fieldOptions.unshift(specialOption);
        
        // Populate dropdown with sorted options
        fieldOptions.forEach(option => {
            const div = document.createElement("div");
            div.textContent = option.text;
            // Style the special option differently
            if (option.id === "__TABLE_DEPENDENCIES__") {
                div.classList.add("font-semibold", "text-blue-600", "dark:text-blue-400");
            }
            div.onclick = () => {
                fieldDropdown.value = option.text;
                document.getElementById("field-dropdown-list").classList.add("hidden");
                if (typeof updateMermaidGraph !== 'undefined') {
                    updateMermaidGraph(tableId, option.id, document.getElementById("flowchart-type").value);
                }
            };
            document.getElementById("field-dropdown-list").appendChild(div);
        });
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

// eNpVkUFvgzAMhf9K5NMmQUWajgKHSSvdeum0Setp0EMEpolWEhSCug7470uLJnU-2Xrfe7LsHgpdIiRQHfWpENxYslvnirh6ylJhZGtr3u6J7z8OG7Sk1grPA1ndbTRphW4aqQ73E7-6QCTttxcMiRVSfY2TlF79bwoHss62vLG62d8qu5MeyHMm34WL_68Ig871klU8qbhfcENSbvbgQY2m5rJ0q_cXQw5WYI05JK4tseLd0eaQq9GhvLP646wKSKzp0AOju4MAl3ds3dQ1Jbe4lvxgeP2HNFx9an07QtLDNyR0RlkYhRFbLuc0pGHA0KfMg7OT5tEsDueLmDG6iBcsHD34uYYEs3iqiNKABQ8x9QBLabV5na5_fcL4C2f3eZE
/*
flowchart TD
    A[Christmas] -->|Get money| B(Go shopping)
    B --> C{Let me think}
    C -->|One| D[Laptop]
    C -->|Two| E[iPhone]
    C -->|Three| F[fa:fa-car Car]
*/


// eNqFVcty2jAU_RWNumlnSIIfOMBk0iGYvGoIgbyg7kJYMlYxlrFlMGSy7bbTx0y76XTZVfed6d_0B9pPqMwrMWSCN5bkc3TPvTpXvoUWwwQWoe2ykeWggIML3fSAeMKo0w2Q7wDecfVgUkOT4bliNckkem3CMuv7yKMkNOGbGTx5bBf3aC12sK1ehs1RQX1uwn_fP38BBrMQp8wLdw4C5FlOwnsx4xEPzwZrZLC3tbWfLNdDve0fd-LqkRxJ-XV1g5i0h8fYKHW1UVQV6u6DpMWlN1qIm-UyflRRmrFUlBa6rqhm6QflsFIoqWxQvxKKdILcNTnxsOc05FzzGlvH1VjI-fPuI2hSTkJwMfYJeBaSYEgtQj2bLdXNuXqujFpHjevyiLQIn6by6RswUAeULIuDZ6t4J4wj_7oijVsHujdaxBp7FqgS7jC8iq_prClJPZ80c3kbz0r1EywKCwzq9QgGnK1Vb1G4c7t7VqdnjdZRaXA6j1fnIWiQQUQDgl-uMio5NNHrrVxpqMqGP2fIHn5KZTiyruKKqwQ1XcpHgmPviWPYj_d2ktcyFjhlHXBIiSCAJg-o113dKCtn5Z5fUd2rV0ZBSoJ__fD313vQZh4BJx4ngUvQUBBByRWd8lD-EwaeuyVdy3tvpUq0AKdTWoLTXtkATh_2BnC67hvA6TptAKfz3gBOG_op8MNGu6FvC7FfG12WjcZJ0vripNf6jGZPvRtkG7vxIW6xqZd__L43x9wYSYs-eqhpDQtl6U1hBvZJ0EcUi7v0NqGakDukT0xYFENMbBS53ISmdyegKOIscTUs8iAiGRiwqOvAoi3uCDGLfIw40SkSWfaXq6LJ2oz1FxQxhcVbGMOitC0pWl7LK7u7sqRJWlYhW5KSgWPxSc5vFzRZLSiKpBZURbvLwMl0EykDCaacBdXZ9T_9C9z9BzEY8TE
/*
flowchart TD
    subgraph tblDrzNazvQ3cSezu["Companies"]
        fldkiNxhdf4UsSw94("🔗 Locations/Branches")
    end
    fldkiNxhdf4UsSw94 <--> fldPsDZpHbxMG2u18
    subgraph tblqxeZvHdLAg6wuM["Branches"]
        fldPsDZpHbxMG2u18("🔗 Company")
    end
    fldPsDZpHbxMG2u18 <--> fldkiNxhdf4UsSw94
    subgraph tblNcDBCsE9A4oqPV["Deals"]
        fldxvkhR25SWdcHMx("→ Sites Type #serviceinfo")
        fldD5CaYGRWCweYet("📝 Lab Acct #")
        fldhsxupWE1yYBDnw("→ Sync Method")
        fldNDoS11kpeS58fd("🔭 Branches Linked to Company")
        fldPQfgOPiORYGAqJ("→ Pts Required?")
        fldE5azDPY5Av42Lp("→ 2nd Sync Method")
        fldswcVxEl3rND18u("f<sub>x</sub> Required Job Fields String")
        fld0202kpE4lVKL91("☑️ Zone Interleaving Allowed?")
    end
    fldkiNxhdf4UsSw94 --> fldNDoS11kpeS58fd
    fldPQfgOPiORYGAqJ --> fldswcVxEl3rND18u
    fldxvkhR25SWdcHMx --> fldswcVxEl3rND18u
    fldhsxupWE1yYBDnw --> fldswcVxEl3rND18u
    fldE5azDPY5Av42Lp --> fldswcVxEl3rND18u
    fld0202kpE4lVKL91 --> fldswcVxEl3rND18u
    fldNDoS11kpeS58fd --> fldswcVxEl3rND18u
    fldD5CaYGRWCweYet --> fldswcVxEl3rND18u
    subgraph tblXij9xpNwUCLRIM["Jobs"]
        fldi0JnXafL7xFdYo("🧻 Required Fields Deal")
    end
    fldswcVxEl3rND18u --> fldi0JnXafL7xFdYo
*/

// export interface State {
//     code: string;
//     mermaid: string;
//     updateDiagram: boolean;
//     autoSync: boolean;
//     rough: boolean;
//     editorMode?: EditorMode;
//     panZoom?: boolean;
//     pan?: { x: number; y: number };
//     zoom?: number;
//     loader?: LoaderConfig;
//   }

function decodeMermaidState() {
    const x = "eNqFVcty2jAU_RWNumlnSIIfOMBk0iGYvGoIgbyg7kJYMlYxlrFlMGSy7bbTx0y76XTZVfed6d_0B9pPqMwrMWSCN5bkc3TPvTpXvoUWwwQWoe2ykeWggIML3fSAeMKo0w2Q7wDecfVgUkOT4bliNckkem3CMuv7yKMkNOGbGTx5bBf3aC12sK1ehs1RQX1uwn_fP38BBrMQp8wLdw4C5FlOwnsx4xEPzwZrZLC3tbWfLNdDve0fd-LqkRxJ-XV1g5i0h8fYKHW1UVQV6u6DpMWlN1qIm-UyflRRmrFUlBa6rqhm6QflsFIoqWxQvxKKdILcNTnxsOc05FzzGlvH1VjI-fPuI2hSTkJwMfYJeBaSYEgtQj2bLdXNuXqujFpHjevyiLQIn6by6RswUAeULIuDZ6t4J4wj_7oijVsHujdaxBp7FqgS7jC8iq_prClJPZ80c3kbz0r1EywKCwzq9QgGnK1Vb1G4c7t7VqdnjdZRaXA6j1fnIWiQQUQDgl-uMio5NNHrrVxpqMqGP2fIHn5KZTiyruKKqwQ1XcpHgmPviWPYj_d2ktcyFjhlHXBIiSCAJg-o113dKCtn5Z5fUd2rV0ZBSoJ__fD313vQZh4BJx4ngUvQUBBByRWd8lD-EwaeuyVdy3tvpUq0AKdTWoLTXtkATh_2BnC67hvA6TptAKfz3gBOG_op8MNGu6FvC7FfG12WjcZJ0vripNf6jGZPvRtkG7vxIW6xqZd__L43x9wYSYs-eqhpDQtl6U1hBvZJ0EcUi7v0NqGakDukT0xYFENMbBS53ISmdyegKOIscTUs8iAiGRiwqOvAoi3uCDGLfIw40SkSWfaXq6LJ2oz1FxQxhcVbGMOitC0pWl7LK7u7sqRJWlYhW5KSgWPxSc5vFzRZLSiKpBZURbvLwMl0EykDCaacBdXZ9T_9C9z9BzEY8TE";
    const compressedGraph = window.Base64.toUint8Array(x, true);
    const graphDefinition = pako.inflate(compressedGraph, { to: "string" });
    console.log("Graph definition:", graphDefinition);
    return graphDefinition;
}

function openInMermaidLive() {
    decodeMermaidState();
    const graphDefinition = localStorage.getItem("lastGraphDefinition");
    if (!graphDefinition) return alert("No diagram available to open in Mermaid Live");
    console.log("Graph definition:", graphDefinition);
    const state = {
        code: graphDefinition,
        mermaid: "{\n  \"theme\": \"default\"\n}",
        autoSync: true,
        rough: false,
        updateDiagram: false,
        panZoom: true,
        // TODO can we get this from the mermaid graph itself?
        // TODO 
        pan: '',
        zoom: '',
        editorMode: "code"
    }
    const compressedGraph = pako.deflate(new TextEncoder().encode(JSON.stringify(state)), { level: 9 });
    const encodedGraph = window.Base64.fromUint8Array(compressedGraph, true);
    const mermaidLiveUrl = `https://mermaid.live/edit#pako:${encodedGraph}`;
    window.open(mermaidLiveUrl, "_blank");
}

function copyMermaidText() {
    const graphDefinition = localStorage.getItem("lastGraphDefinition");
    if (!graphDefinition) return alert("No diagram available to copy");
    navigator.clipboard.writeText(graphDefinition).then(() => {
        alert("Mermaid diagram copied to clipboard");
    }).catch(error => {
        console.error("Error copying to clipboard:", error);
        alert("Failed to copy Mermaid diagram to clipboard");
    });
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

// Formula Compressor functions
function filterCompressorTableDropdown() {
    const input = document.getElementById("compressor-table-dropdown");
    const list = document.getElementById("compressor-table-dropdown-list");
    const filter = input.value.toLowerCase();
    list.innerHTML = "";
    list.classList.remove("hidden");

    const filteredOptions = compressorTableOptions.filter(option =>
        option.text.toLowerCase().includes(filter)
    );

    filteredOptions.forEach(option => {
        const div = document.createElement("div");
        div.classList.add("p-2", "cursor-pointer", "hover:bg-gray-200", "dark:hover:bg-gray-600", "dark:text-white");
        div.textContent = option.text;
        div.onclick = () => {
            input.value = option.text;
            list.classList.add("hidden");
            updateCompressorFieldDropdown(option.id);
            // Enable the Table Report button when a table is selected
            const tableReportBtn = document.getElementById("table-report-btn");
            if (tableReportBtn) {
                tableReportBtn.disabled = false;
            }
        };
        list.appendChild(div);
    });

    if (filteredOptions.length === 0) {
        const noResultsDiv = document.createElement("div");
        noResultsDiv.classList.add("p-2", "text-gray-500", "dark:text-gray-400");
        noResultsDiv.textContent = "No tables found";
        list.appendChild(noResultsDiv);
    }
}

function filterCompressorFieldDropdown() {
    const input = document.getElementById("compressor-field-dropdown");
    const list = document.getElementById("compressor-field-dropdown-list");
    const filter = input.value.toLowerCase();
    list.innerHTML = "";
    list.classList.remove("hidden");

    const filteredOptions = compressorFieldOptions.filter(option =>
        option.text.toLowerCase().includes(filter)
    );

    filteredOptions.forEach(option => {
        const div = document.createElement("div");
        div.classList.add("p-2", "cursor-pointer", "hover:bg-gray-200", "dark:hover:bg-gray-600", "dark:text-white");
        div.textContent = option.text;
        div.onclick = () => {
            input.value = option.text;
            list.classList.add("hidden");
            // Update the original formula display
            updateOriginalFormulaDisplay(option.tableId, option.id, option.formula);
        };
        list.appendChild(div);
    });

    if (filteredOptions.length === 0) {
        const noResultsDiv = document.createElement("div");
        noResultsDiv.classList.add("p-2", "text-gray-500", "dark:text-gray-400");
        noResultsDiv.textContent = "No formula fields found";
        list.appendChild(noResultsDiv);
    }
}

function updateCompressorFieldDropdown(tableId) {
    const schemaData = JSON.parse(localStorage.getItem("airtableSchema"));
    const fieldDropdown = document.getElementById("compressor-field-dropdown");
    
    // Clear the field input value
    fieldDropdown.value = "";
    
    compressorFieldOptions = [];

    if (schemaData?.schema?.tables) {
        const selectedTable = schemaData.schema.tables.find(table => table.id === tableId);
        selectedTable?.fields.forEach(field => {
            // Only include formula fields
            if (field.type === "formula") {
                const option = {
                    id: field.id,
                    text: field.name,
                    tableId: tableId,
                    formula: field.options?.formula || ""
                };
                compressorFieldOptions.push(option);
            }
        });
        
        // Sort fields alphabetically
        compressorFieldOptions.sort((a, b) => a.text.localeCompare(b.text));
    }
    
    // Clear displays
    document.getElementById("original-formula-display").innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">No formula selected</span>';
    document.getElementById("compressed-formula-display").innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">Select a formula field to see compressed results</span>';
}

function updateOriginalFormulaDisplay(tableId, fieldId, formula) {
    // Store the original formula (in field ID format)
    originalFormulaText = formula || "";
    
    const originalDisplay = document.getElementById("original-formula-display");
    
    if (!originalFormulaText) {
        originalDisplay.textContent = "No formula available";
        return;
    }
    
    // Get the current output format
    const formatSelect = document.getElementById("output-format");
    const outputFormat = formatSelect ? formatSelect.value : "field_ids";
    
    // Convert and display based on format
    updateOriginalFormulaFormat(outputFormat);
    
    // Auto-compress the formula
    autoCompressFormula();
}

function updateOriginalFormulaFormat(outputFormat) {
    const originalDisplay = document.getElementById("original-formula-display");
    
    if (!originalFormulaText) {
        return;
    }
    
    // Call Python function to convert the formula
    if (typeof window.convertFormulaDisplay !== 'undefined') {
        const convertedFormula = window.convertFormulaDisplay(originalFormulaText, outputFormat);
        
        // Apply display formatting
        const displayFormat = getDisplayFormat();
        const formattedFormula = applyDisplayFormat(convertedFormula, displayFormat);
        
        originalDisplay.textContent = formattedFormula;
    } else {
        // Fallback if Python not ready
        originalDisplay.textContent = originalFormulaText;
    }
}

function onOutputFormatChange() {
    const formatSelect = document.getElementById("output-format");
    if (formatSelect && originalFormulaText) {
        updateOriginalFormulaFormat(formatSelect.value);
        autoCompressFormula();
    }
}

function onDisplayFormatChange() {
    // Re-format both original and compressed formulas
    const formatSelect = document.getElementById("output-format");
    if (formatSelect && originalFormulaText) {
        updateOriginalFormulaFormat(formatSelect.value);
    }
    
    // Re-format compressed formula if it exists
    const compressedDisplay = document.getElementById("compressed-formula-display");
    if (compressedDisplay && compressedDisplay.textContent && 
        !compressedDisplay.textContent.includes("Select a formula field")) {
        // Store and re-format the compressed formula
        const rawText = compressedDisplay.getAttribute('data-raw-formula');
        if (rawText) {
            const displayFormat = getDisplayFormat();
            const formattedFormula = applyDisplayFormat(rawText, displayFormat);
            compressedDisplay.textContent = formattedFormula;
        }
    }
}

function getDisplayFormat() {
    const displayFormatSelect = document.getElementById("display-format");
    return displayFormatSelect ? displayFormatSelect.value : "compact";
}

function applyDisplayFormat(formula, displayFormat) {
    if (displayFormat === "logical") {
        if (typeof window.formatFormulaLogical !== 'undefined') {
            return window.formatFormulaLogical(formula);
        }
    } else {
        if (typeof window.formatFormulaCompact !== 'undefined') {
            return window.formatFormulaCompact(formula);
        }
    }
    return formula;
}

function compressFormula() {
    const tableInput = document.getElementById("compressor-table-dropdown");
    const fieldInput = document.getElementById("compressor-field-dropdown");
    const depthInput = document.getElementById("compression-depth");
    const formatSelect = document.getElementById("output-format");
    const displayFormatSelect = document.getElementById("display-format");
    
    const tableName = tableInput.value.trim();
    const fieldName = fieldInput.value.trim();
    
    if (!tableName || !fieldName) {
        alert("Please select both a table and a field.");
        return;
    }
    
    // Get optional parameters
    const depthValue = depthInput.value.trim();
    const compressionDepth = depthValue ? parseInt(depthValue) : null;
    const outputFormat = formatSelect.value;
    const displayFormat = displayFormatSelect.value;
    
    // Call Python function
    if (typeof window.compressFormulaFromUI !== 'undefined') {
        window.compressFormulaFromUI(tableName, fieldName, compressionDepth, outputFormat, displayFormat);
    } else {
        alert("Formula compression is not yet initialized. Please refresh the page.");
    }
}

function autoCompressFormula() {
    const tableInput = document.getElementById("compressor-table-dropdown");
    const fieldInput = document.getElementById("compressor-field-dropdown");
    
    const tableName = tableInput ? tableInput.value.trim() : "";
    const fieldName = fieldInput ? fieldInput.value.trim() : "";
    
    // Only auto-compress if both table and field are selected
    if (tableName && fieldName && originalFormulaText) {
        compressFormula();
    }
}

// Make function available globally for inline event handlers
window.autoCompressFormula = autoCompressFormula;

function copyCompressedFormula() {
    const compressedDisplay = document.getElementById("compressed-formula-display");
    const text = compressedDisplay.textContent;
    
    if (!text || text.includes("Select a formula field")) {
        alert("No compressed formula to copy");
        return;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        alert("Compressed formula copied to clipboard");
    }).catch(error => {
        console.error("Error copying to clipboard:", error);
        alert("Failed to copy compressed formula to clipboard");
    });
}

function generateTableReport() {
    const tableInput = document.getElementById("compressor-table-dropdown");
    const depthInput = document.getElementById("compression-depth");
    
    const tableName = tableInput.value.trim();
    
    if (!tableName) {
        alert("Please select a table.");
        return;
    }
    
    // Get compression depth
    const depthValue = depthInput.value.trim();
    const compressionDepth = depthValue ? parseInt(depthValue) : null;
    
    // Call Python function to generate CSV data
    if (typeof window.generateTableReportData !== 'undefined') {
        try {
            const csvData = window.generateTableReportData(tableName, compressionDepth);
            
            // Download the CSV
            const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });
            const link = document.createElement("a");
            const url = URL.createObjectURL(blob);
            
            // Create filename with table name and timestamp
            const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
            const filename = `${tableName}_formula_report_${timestamp}.csv`;
            
            link.setAttribute("href", url);
            link.setAttribute("download", filename);
            link.style.visibility = "hidden";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            alert(`Table report generated successfully for "${tableName}"!`);
        } catch (error) {
            console.error("Error generating table report:", error);
            alert(`Failed to generate table report: ${error.message || error}`);
        }
    } else {
        alert("Table report generation is not yet initialized. Please refresh the page.");
    }
}

function initializeCompressorDropdowns() {
    const schemaData = JSON.parse(localStorage.getItem("airtableSchema"));
    
    compressorTableOptions = [];
    compressorFieldOptions = [];

    if (schemaData?.schema?.tables) {
        schemaData.schema.tables.forEach(table => {
            const option = {
                id: table.id,
                text: table.name
            };
            compressorTableOptions.push(option);
        });
        
        // Sort tables alphabetically
        compressorTableOptions.sort((a, b) => a.text.localeCompare(b.text));
    }
    
    // Also initialize analysis table options
    initializeAnalysisDropdowns();
    
    // Also initialize grapher table options
    initializeGrapherDropdowns();
}

// Table Analysis functions
function initializeAnalysisDropdowns() {
    const schemaData = JSON.parse(localStorage.getItem("airtableSchema"));
    
    analysisTableOptions = [];

    if (schemaData?.schema?.tables) {
        schemaData.schema.tables.forEach(table => {
            const option = {
                id: table.id,
                text: table.name
            };
            analysisTableOptions.push(option);
        });
        
        // Sort tables alphabetically
        analysisTableOptions.sort((a, b) => a.text.localeCompare(b.text));
    }
}

function filterAnalysisTableDropdown() {
    const input = document.getElementById("analysis-table-dropdown");
    const list = document.getElementById("analysis-table-dropdown-list");
    const filter = input.value.toLowerCase();
    list.innerHTML = "";
    list.classList.remove("hidden");

    const filteredOptions = analysisTableOptions.filter(option =>
        option.text.toLowerCase().includes(filter)
    );

    filteredOptions.forEach(option => {
        const div = document.createElement("div");
        div.classList.add("p-2", "cursor-pointer", "hover:bg-gray-200", "dark:hover:bg-gray-600", "dark:text-white");
        div.textContent = option.text;
        div.onclick = () => {
            input.value = option.text;
            list.classList.add("hidden");
            // Enable the generate button when a table is selected
            const generateBtn = document.getElementById("generate-table-complexity-btn");
            if (generateBtn) {
                generateBtn.disabled = false;
            }
        };
        list.appendChild(div);
    });

    if (filteredOptions.length === 0) {
        const noResultsDiv = document.createElement("div");
        noResultsDiv.classList.add("p-2", "text-gray-500", "dark:text-gray-400");
        noResultsDiv.textContent = "No tables found";
        list.appendChild(noResultsDiv);
    }
}

function generateTableComplexityCSV() {
    const tableInput = document.getElementById("analysis-table-dropdown");
    const tableName = tableInput.value.trim();
    
    if (!tableName) {
        alert("Please select a table.");
        return;
    }
    
    // Call Python function to generate CSV data
    if (typeof window.getTableComplexityData !== 'undefined') {
        try {
            const csvData = window.getTableComplexityData(tableName);
            
            if (!csvData || csvData.length === 0) {
                alert("No complexity data found for this table.");
                return;
            }
            
            // Store the CSV data
            lastAnalysisCSV = csvData;
            
            // Display the CSV data
            const csvOutput = document.getElementById("analysis-csv-output");
            const resultsDiv = document.getElementById("analysis-results");
            
            // Convert array to CSV string for display
            const csvString = csvData.map(row => row.join(",")).join("\n");
            csvOutput.textContent = csvString;
            
            // Show results
            resultsDiv.classList.remove("hidden");
            
        } catch (error) {
            console.error("Error generating table complexity:", error);
            alert(`Failed to generate table complexity: ${error.message || error}`);
        }
    } else {
        alert("Table complexity analysis is not yet initialized. Please refresh the page.");
    }
}

function downloadTableComplexityCSV() {
    if (!lastAnalysisCSV || lastAnalysisCSV.length === 0) {
        alert("No data to download");
        return;
    }
    
    const tableInput = document.getElementById("analysis-table-dropdown");
    const tableName = tableInput.value.trim();
    
    // Convert array to CSV string
    const csvString = lastAnalysisCSV.map(row => row.join(",")).join("\n");
    
    // Download the CSV
    const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    
    // Create filename with table name
    const filename = `${tableName}_field_complexity.csv`;
    
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Formula Grapher functions
function initializeGrapherDropdowns() {
    const schemaData = JSON.parse(localStorage.getItem("airtableSchema"));
    
    grapherTableOptions = [];
    grapherFieldOptions = [];

    if (schemaData?.schema?.tables) {
        schemaData.schema.tables.forEach(table => {
            const option = {
                id: table.id,
                text: table.name
            };
            grapherTableOptions.push(option);
        });
        
        // Sort tables alphabetically
        grapherTableOptions.sort((a, b) => a.text.localeCompare(b.text));
    }
}

function filterGrapherTableDropdown() {
    const input = document.getElementById("grapher-table-dropdown");
    const list = document.getElementById("grapher-table-dropdown-list");
    const filter = input.value.toLowerCase();
    list.innerHTML = "";
    list.classList.remove("hidden");

    const filteredOptions = grapherTableOptions.filter(option =>
        option.text.toLowerCase().includes(filter)
    );

    filteredOptions.forEach(option => {
        const div = document.createElement("div");
        div.classList.add("p-2", "cursor-pointer", "hover:bg-gray-200", "dark:hover:bg-gray-600", "dark:text-white");
        div.textContent = option.text;
        div.onclick = () => {
            input.value = option.text;
            list.classList.add("hidden");
            updateGrapherFieldDropdown(option.id);
        };
        list.appendChild(div);
    });

    if (filteredOptions.length === 0) {
        const noResultsDiv = document.createElement("div");
        noResultsDiv.classList.add("p-2", "text-gray-500", "dark:text-gray-400");
        noResultsDiv.textContent = "No tables found";
        list.appendChild(noResultsDiv);
    }
}

function filterGrapherFieldDropdown() {
    const input = document.getElementById("grapher-field-dropdown");
    const list = document.getElementById("grapher-field-dropdown-list");
    const filter = input.value.toLowerCase();
    list.innerHTML = "";
    list.classList.remove("hidden");

    const filteredOptions = grapherFieldOptions.filter(option =>
        option.text.toLowerCase().includes(filter)
    );

    filteredOptions.forEach(option => {
        const div = document.createElement("div");
        div.classList.add("p-2", "cursor-pointer", "hover:bg-gray-200", "dark:hover:bg-gray-600", "dark:text-white");
        div.textContent = option.text;
        div.onclick = () => {
            input.value = option.text;
            list.classList.add("hidden");
            onGrapherFieldSelected(option.tableName, option.text);
        };
        list.appendChild(div);
    });

    if (filteredOptions.length === 0) {
        const noResultsDiv = document.createElement("div");
        noResultsDiv.classList.add("p-2", "text-gray-500", "dark:text-gray-400");
        noResultsDiv.textContent = "No formula fields found";
        list.appendChild(noResultsDiv);
    }
}

function updateGrapherFieldDropdown(tableId) {
    const schemaData = JSON.parse(localStorage.getItem("airtableSchema"));
    const fieldDropdown = document.getElementById("grapher-field-dropdown");
    
    // Clear the field input value
    fieldDropdown.value = "";
    
    grapherFieldOptions = [];
    
    // Find table name
    let tableName = "";

    if (schemaData?.schema?.tables) {
        const selectedTable = schemaData.schema.tables.find(table => table.id === tableId);
        if (selectedTable) {
            tableName = selectedTable.name;
            selectedTable.fields.forEach(field => {
                // Only include formula fields
                if (field.type === "formula") {
                    const option = {
                        id: field.id,
                        text: field.name,
                        tableId: tableId,
                        tableName: tableName,
                        formula: field.options?.formula || ""
                    };
                    grapherFieldOptions.push(option);
                }
            });
        }
        
        // Sort fields alphabetically
        grapherFieldOptions.sort((a, b) => a.text.localeCompare(b.text));
    }
    
    // Clear displays
    document.getElementById("grapher-formula-display").innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">Select a formula field to see its formula</span>';
    document.getElementById("formula-grapher-mermaid-container").innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">Select a formula field to generate flowchart</span>';
}

function onGrapherFieldSelected(tableName, fieldName) {
    // Update formula display
    if (typeof window.getFormulaForDisplay !== 'undefined') {
        const formula = window.getFormulaForDisplay(tableName, fieldName);
        const formulaDisplay = document.getElementById("grapher-formula-display");
        if (formula) {
            formulaDisplay.textContent = formula;
        } else {
            formulaDisplay.innerHTML = '<span class="text-gray-500 dark:text-gray-400 italic">No formula available</span>';
        }
    }
    
    // Auto-generate the flowchart
    autoGenerateFormulaGraph();
}

function autoGenerateFormulaGraph() {
    const tableInput = document.getElementById("grapher-table-dropdown");
    const fieldInput = document.getElementById("grapher-field-dropdown");
    
    const tableName = tableInput ? tableInput.value.trim() : "";
    const fieldName = fieldInput ? fieldInput.value.trim() : "";
    
    if (!tableName || !fieldName) {
        return;
    }
    
    // Get options
    const expandCheckbox = document.getElementById("grapher-expand-fields");
    const depthInput = document.getElementById("grapher-expansion-depth");
    const directionDropdown = document.getElementById("grapher-flowchart-direction");
    
    const expandFields = expandCheckbox ? expandCheckbox.checked : false;
    const direction = directionDropdown ? directionDropdown.value : "TD";
    const depthValue = depthInput ? depthInput.value.trim() : "1";
    const maxDepth = depthValue ? parseInt(depthValue) : 1;
    
    // Call Python function
    if (typeof window.graphFormulaFromUI !== 'undefined') {
        window.graphFormulaFromUI(tableName, fieldName, expandFields, maxDepth, direction);
    }
}

function downloadFormulaGrapherSVG() {
    const svgElement = document.querySelector("#formula-grapher-mermaid-container .mermaid svg");
    if (!svgElement) return alert("No diagram available to download");
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: "image/svg+xml" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "formula_flowchart.svg";
    link.click();
}

function openFormulaGrapherInMermaidLive() {
    const graphDefinition = localStorage.getItem("lastFormulaGraphDefinition");
    if (!graphDefinition) return alert("No diagram available to open in Mermaid Live");
    
    const state = {
        code: graphDefinition,
        mermaid: "{\n  \"theme\": \"default\"\n}",
        autoSync: true,
        rough: false,
        updateDiagram: false,
        panZoom: true,
        pan: '',
        zoom: '',
        editorMode: "code"
    }
    const compressedGraph = pako.deflate(new TextEncoder().encode(JSON.stringify(state)), { level: 9 });
    const encodedGraph = window.Base64.fromUint8Array(compressedGraph, true);
    const mermaidLiveUrl = `https://mermaid.live/edit#pako:${encodedGraph}`;
    window.open(mermaidLiveUrl, "_blank");
}

function copyFormulaGrapherMermaidText() {
    const graphDefinition = localStorage.getItem("lastFormulaGraphDefinition");
    if (!graphDefinition) return alert("No diagram available to copy");
    navigator.clipboard.writeText(graphDefinition).then(() => {
        alert("Mermaid diagram copied to clipboard");
    }).catch(error => {
        console.error("Error copying to clipboard:", error);
        alert("Failed to copy Mermaid diagram to clipboard");
    });
}

function toggleFormulaGrapherFullscreen() {
    const mermaidContainer = document.getElementById("formula-grapher-mermaid-container");
    if (!document.fullscreenElement) {
        mermaidContainer?.requestFullscreen().catch(err => {
            alert(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
        });
    } else {
        document.exitFullscreen();
    }
}


// Generic copy to clipboard function for code boxes
function copyToClipboard(elementId, description = "Content", event) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    if (!text || text.includes("No formula selected") || text.includes("Select a formula field")) {
        alert(`No ${description.toLowerCase()} to copy`);
        return;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        // Visual feedback - briefly change the button
        if (event && event.currentTarget) {
            const button = event.currentTarget;
            const originalHTML = button.innerHTML;
            button.innerHTML = '<svg class="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
            button.style.opacity = '100';
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.style.opacity = '';
            }, 1500);
        }
    }).catch(error => {
        console.error("Error copying to clipboard:", error);
        alert(`Failed to copy ${description.toLowerCase()} to clipboard`);
    });
}

// Export functions to window object so they can be called from HTML
window.fetchSchema = fetchSchema;
window.downloadMermaidSVG = downloadMermaidSVG;
window.openInMermaidLive = openInMermaidLive;
window.copyMermaidText = copyMermaidText;
window.toggleFullscreen = toggleFullscreen;
window.downloadMermaidText = downloadMermaidText;
window.filterTableDropdown = filterTableDropdown;
window.filterFieldDropdown = filterFieldDropdown;
window.switchTab = switchTab;
window.filterCompressorTableDropdown = filterCompressorTableDropdown;
window.filterCompressorFieldDropdown = filterCompressorFieldDropdown;
window.compressFormula = compressFormula;
window.copyCompressedFormula = copyCompressedFormula;
window.generateTableReport = generateTableReport;
window.copyToClipboard = copyToClipboard;
window.filterAnalysisTableDropdown = filterAnalysisTableDropdown;
window.generateTableComplexityCSV = generateTableComplexityCSV;
window.downloadTableComplexityCSV = downloadTableComplexityCSV;
window.filterGrapherTableDropdown = filterGrapherTableDropdown;
window.filterGrapherFieldDropdown = filterGrapherFieldDropdown;
window.downloadFormulaGrapherSVG = downloadFormulaGrapherSVG;
window.openFormulaGrapherInMermaidLive = openFormulaGrapherInMermaidLive;
window.copyFormulaGrapherMermaidText = copyFormulaGrapherMermaidText;
window.toggleFormulaGrapherFullscreen = toggleFormulaGrapherFullscreen;
