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

window.fetchSchema = fetchSchema;
window.downloadMermaidSVG = downloadMermaidSVG;
window.openInMermaidLive = openInMermaidLive;
window.copyMermaidText = copyMermaidText;
window.toggleFullscreen = toggleFullscreen;
window.downloadMermaidText = downloadMermaidText;