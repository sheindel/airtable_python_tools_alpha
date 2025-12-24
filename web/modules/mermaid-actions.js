import { toast } from "./toast.js";

function decodeMermaidState() {
    const x = "eNqFVcty2jAU_RWNumlnSIIfOMBk0iGYvGoIgbyg7kJYMlYxlrFlMGSy7bbTx0y76XTZVfed6d_0B9pPqMwrMWSCN5bkc3TPvTpXvoUWwwQWoe2ykeWggIML3fSAeMKo0w2Q7wDecfVgUkOT4bliNckkem3CMuv7yKMkNOGbGTx5bBf3aC12sK1ehs1RQX1uwn_fP38BBrMQp8wLdw4C5FlOwnsx4xEPzwZrZLC3tbWfLNdDve0fd-LqkRxJ-XV1g5i0h8fYKHW1UVQV6u6DpMWlN1qIm-UyflRRmrFUlBa6rqhm6QflsFIoqWxQvxKKdILcNTnxsOc05FzzGlvH1VjI-fPuI2hSTkJwMfYJeBaSYEgtQj2bLdXNuXqujFpHjevyiLQIn6by6RswUAeULIuDZ6t4J4wj_7oijVsHujdaxBp7FqgS7jC8iq_prClJPZ80c3kbz0r1EywKCwzq9QgGnK1Vb1G4c7t7VqdnjdZRaXA6j1fnIWiQQUQDgl-uMio5NNHrrVxpqMqGP2fIHn5KZTiyruKKqwQ1XcpHgmPviWPYj_d2ktcyFjhlHXBIiSCAJg-o113dKCtn5Z5fUd2rV0ZBSoJ__fD313vQZh4BJx4ngUvQUBBByRWd8lD-EwaeuyVdy3tvpUq0AKdTWoLTXtkATh_2BnC67hvA6TptAKfz3gBOG_op8MNGu6FvC7FfG12WjcZJ0vripNf6jGZPvRtkG7vxIW6xqZd__L43x9wYSYs-eqhpDQtl6U1hBvZJ0EcUi7v0NqGakDukT0xYFENMbBS53ISmdyegKOIscTUs8iAiGRiwqOvAoi3uCDGLfIw40SkSWfaXq6LJ2oz1FxQxhcVbGMOitC0pWl7LK7u7sqRJWlYhW5KSgWPxSc5vFzRZLSiKpBZURbvLwMl0EykDCaacBdXZ9T_9C9z9BzEY8TE";
    const compressedGraph = window.Base64.toUint8Array(x, true);
    const graphDefinition = window.pako.inflate(compressedGraph, { to: "string" });
    console.log("Graph definition:", graphDefinition);
    return graphDefinition;
}

export function openInMermaidLive() {
    decodeMermaidState();
    const graphDefinition = localStorage.getItem("lastGraphDefinition");
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
        editorMode: "code"
    };
    const compressedGraph = window.pako.deflate(new TextEncoder().encode(JSON.stringify(state)), { level: 9 });
    const encodedGraph = window.Base64.fromUint8Array(compressedGraph, true);
    const mermaidLiveUrl = `https://mermaid.live/edit#pako:${encodedGraph}`;
    window.open(mermaidLiveUrl, "_blank");
}

export function copyMermaidText() {
    const graphDefinition = localStorage.getItem("lastGraphDefinition");
    if (!graphDefinition) return toast.warning("No diagram available to copy");
    navigator.clipboard.writeText(graphDefinition).then(() => {
        toast.success("Mermaid diagram copied to clipboard");
    }).catch((error) => {
        console.error("Error copying to clipboard:", error);
        toast.error("Failed to copy Mermaid diagram to clipboard");
    });
}

export function toggleFullscreen() {
    const mermaidContainer = document.getElementById("mermaid-container");
    if (!document.fullscreenElement) {
        mermaidContainer?.requestFullscreen().catch((err) => {
            toast.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
        });
    } else {
        document.exitFullscreen();
    }
}

export function downloadMermaidText() {
    const graphDefinition = localStorage.getItem("lastGraphDefinition");
    if (!graphDefinition) return toast.warning("No diagram available to download");
    const blob = new Blob([graphDefinition], { type: "text/plain" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "diagram.mmd";
    link.click();
}

export function downloadMermaidSVG() {
    const svgElement = document.querySelector(".mermaid svg");
    if (!svgElement) return toast.warning("No diagram available to download");
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: "image/svg+xml" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "diagram.svg";
    link.click();
}
