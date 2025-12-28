"""Formula Evaluator Tab - Evaluate formulas by substituting values"""
from pyscript import document, window
import re
from typing import Literal
import sys
sys.path.append("web")
from components.airtable_client import get_local_storage_metadata
from at_metadata_graph import metadata_to_graph
from airtable_formula_evaluator import evaluate_formula, substitute_field_values, get_unresolved_fields, simplify_formula, FormulaEvaluationError


def _convert_field_references(
    formula: str,
    metadata: dict,
    output_format: Literal["field_ids", "field_names"]
) -> str:
    """Convert field references in a formula to the desired format.
    
    Args:
        formula: The formula text
        metadata: Airtable metadata
        output_format: "field_ids" or "field_names"
    
    Returns:
        Formula with converted field references
    """
    if output_format == "field_ids":
        # Already in field ID format, return as is
        return formula
    
    # Convert to field names
    from components.airtable_client import find_field_by_id
    field_id_pattern = r'\{(fld[a-zA-Z0-9]+)\}'
    
    def replace_with_name(match):
        field_id = match.group(1)
        field = find_field_by_id(metadata, field_id)
        if field:
            return f"{{{field['name']}}}"
        return match.group(0)  # Return original if field not found
    
    return re.sub(field_id_pattern, replace_with_name, formula)


def get_formula_dependencies(field_id: str, metadata: dict) -> list[dict]:
    """
    Get all leaf dependencies for a formula or rollup field.
    Returns list of field info dicts with: id, name, type, table_name
    """
    G = metadata_to_graph(metadata)
    
    # Get all ancestors (what this field depends on)
    ancestors = set()
    to_visit = [field_id]
    visited = set()
    
    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)
        
        # Get predecessors (fields this one depends on)
        for pred in G.predecessors(current):
            if G.nodes[pred].get("type") == "field":
                ancestors.add(pred)
                to_visit.append(pred)
    
    # Filter to leaf nodes only (non-formula, non-rollup, non-lookup)
    leaf_dependencies = []
    for field_id in ancestors:
        if field_id not in G.nodes:
            continue
            
        field_data = G.nodes[field_id].get("metadata", {})
        field_type = field_data.get("type", "")
        
        # Only include leaf fields (not computed fields)
        if field_type not in ["formula", "rollup", "multipleLookupValues", "count"]:
            leaf_dependencies.append({
                "id": field_id,
                "name": field_data.get("name", field_id),
                "type": field_type,
                "table_name": G.nodes[field_id].get("table_name", "")
            })
    
    return sorted(leaf_dependencies, key=lambda x: (x["table_name"], x["name"]))


def load_field_dependencies():
    """Called when a field is selected - loads its dependencies"""
    try:
        table_dropdown = document.getElementById("eval-table-dropdown")
        field_dropdown = document.getElementById("eval-field-dropdown")
        output_format_select = document.getElementById("eval-output-format")
        
        if not table_dropdown or not field_dropdown:
            print("Dropdowns not found")
            return
        
        # Get output format setting
        output_format = output_format_select.value if output_format_select else "field_names"
        
        # Use selectedId to get the actual IDs instead of display text
        table_id = table_dropdown.selectedId
        field_id = field_dropdown.selectedId
        
        print(f"Loading dependencies for table={table_id}, field={field_id}")
        
        if not table_id or not field_id:
            print("No table or field selected")
            return
        
        # Save existing input values before rebuilding the form
        saved_values = {}
        existing_inputs = document.querySelectorAll(".eval-input")
        for input_elem in existing_inputs:
            field_id_attr = input_elem.getAttribute("data-field-id")
            if field_id_attr and input_elem.value:
                saved_values[field_id_attr] = input_elem.value
        print(f"Saved input values: {saved_values}")
        
        metadata = get_local_storage_metadata()
        if not metadata:
            print("No metadata available")
            return
        
        # Find the field by ID
        target_field = None
        target_table_name = ""
        for table in metadata["tables"]:
            if table["id"] == table_id:
                target_table_name = table["name"]
                for field in table["fields"]:
                    if field["id"] == field_id:
                        target_field = field
                        break
                break
        
        if not target_field:
            return
        
        # Check if it's a formula or rollup
        field_type = target_field.get("type", "")
        if field_type not in ["formula", "rollup"]:
            result_div = document.getElementById("eval-result")
            result_div.innerHTML = """
                <div class="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
                    <p class="text-yellow-800 dark:text-yellow-200">
                        ⚠️ Selected field must be a formula or rollup field.
                    </p>
                </div>
            """
            return
        
        # Get the formula
        formula = ""
        if field_type == "formula":
            formula = target_field.get("options", {}).get("formula", "")
        elif field_type == "rollup":
            # For rollups, show the aggregation function
            function = target_field.get("options", {}).get("formulaTextAfterReferencedFieldName", "SUM")
            linked_field_id = target_field.get("options", {}).get("fieldIdInLinkedTable", "")
            formula = f"{function}({{linked_field}})"
        
        if not formula:
            return
        
        # Convert formula to desired output format
        formula_display = _convert_field_references(formula, metadata, output_format)
        
        # Get dependencies
        dependencies = get_formula_dependencies(target_field["id"], metadata)
        
        # Build the input form
        html_parts = [f"""
            <div class="space-y-4">
                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <h3 class="font-semibold mb-2 text-gray-900 dark:text-white">Formula:</h3>
                    <pre class="text-sm bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-600 overflow-x-auto"><code class="text-gray-900 dark:text-gray-100">{formula_display}</code></pre>
                </div>
        """]
        
        if dependencies:
            html_parts.append("""
                <div>
                    <h3 class="font-semibold mb-3 text-gray-900 dark:text-white">Enter Values:</h3>
                    <div class="space-y-3">
            """)
            
            for dep in dependencies:
                field_label = f"{dep['table_name']}.{dep['name']}" if dep['table_name'] != target_table_name else dep['name']
                html_parts.append(f"""
                    <div class="flex items-center gap-3">
                        <label class="w-1/3 text-sm font-medium text-gray-700 dark:text-gray-300 truncate" 
                               title="{field_label}">
                            {field_label}
                        </label>
                        <input type="text" 
                               id="input-{dep['id']}" 
                               data-field-id="{dep['id']}"
                               data-field-type="{dep['type']}"
                               class="flex-1 p-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white eval-input"
                               placeholder="Enter value...">
                    </div>
                """)
            
            # Store formula and dependency IDs as data attributes to avoid escaping issues
            dep_ids_json = str([d["id"] for d in dependencies]).replace("'", '"')
            html_parts.append(f"""
                    </div>
                    <button id="eval-calculate-btn" 
                            class="mt-4 bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2 px-4 rounded-lg"
                            data-field-id="{target_field['id']}"
                            data-dependencies='{dep_ids_json}'>
                        Evaluate Formula
                    </button>
                </div>
            """)
        else:
            html_parts.append("""
                <div class="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                    <p class="text-blue-800 dark:text-blue-200">
                        ℹ️ This formula has no dependencies on other fields.
                    </p>
                </div>
            """)
        
        html_parts.append("</div>")
        
        result_div = document.getElementById("eval-result")
        result_div.innerHTML = "".join(html_parts)
        
        # Clear any previous evaluation results
        eval_output_div = document.getElementById("eval-output")
        if eval_output_div:
            eval_output_div.innerHTML = ""
        
        # Restore saved input values
        for field_id, value in saved_values.items():
            input_elem = document.getElementById(f"input-{field_id}")
            if input_elem:
                input_elem.value = value
                print(f"Restored value for {field_id}: {value}")
    
    except Exception as e:
        import traceback
        print("Error loading dependencies:", traceback.format_exc())


def evaluate_formula_with_values(field_id: str, dependency_ids: list, output_format: str = "field_names"):
    """Evaluate the formula with user-entered values
    
    Args:
        field_id: The field ID to evaluate
        dependency_ids: List of dependency field IDs
        output_format: "field_ids" or "field_names" for display
    """
    try:
        print(f"Evaluating formula for field {field_id} with dependencies {dependency_ids}")
        
        # Get the formula from metadata
        metadata = get_local_storage_metadata()
        if not metadata:
            print("No metadata available")
            return
        
        # Find the field to get its formula
        formula = None
        for table in metadata["tables"]:
            for field in table["fields"]:
                if field["id"] == field_id:
                    if field["type"] == "formula":
                        formula = field.get("options", {}).get("formula", "")
                    elif field["type"] == "rollup":
                        function = field.get("options", {}).get("formulaTextAfterReferencedFieldName", "SUM")
                        formula = f"{function}({{linked_field}})"
                    break
            if formula:
                break
        
        if not formula:
            print(f"No formula found for field {field_id}")
            result_div = document.getElementById("eval-result")
            result_div.innerHTML += """
                <div class="mt-4 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg">
                    <p class="text-red-800 dark:text-red-200">❌ Error: Could not find formula for this field.</p>
                </div>
            """
            return
        
        print(f"Formula: {formula}")
        
        # Convert formula for display
        formula_display = _convert_field_references(formula, metadata, output_format)
        
        # Get input values
        values = {}
        for dep_id in dependency_ids:
            input_elem = document.getElementById(f"input-{dep_id}")
            if input_elem and input_elem.value.strip():
                values[dep_id] = input_elem.value.strip()
        
        print(f"Input values: {values}")
        
        # Replace field references with values using the evaluator module
        formula_with_values = substitute_field_values(formula, values)
        
        print(f"Formula after substitution: {formula_with_values}")
        
        # Try to simplify the formula
        simplified_formula = simplify_formula(formula_with_values)
        
        print(f"Formula after simplification: {simplified_formula}")
        
        # Show the formula with substituted values
        result_div = document.getElementById("eval-result")
        
        # Check if there are still unresolved fields
        remaining_refs = get_unresolved_fields(simplified_formula)
        
        if remaining_refs:
            # Build a map of field ID to name for display
            field_names = {}
            for table in metadata["tables"]:
                for field in table["fields"]:
                    field_names[field["id"]] = field["name"]
            
            unresolved_names = [field_names.get(ref, ref) for ref in remaining_refs]
            result_html = f"""
                <div class="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg">
                    <h4 class="font-semibold mb-2 text-yellow-900 dark:text-yellow-100">Partially Evaluated:</h4>
                    <pre class="text-sm bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-600 overflow-x-auto"><code class="text-gray-900 dark:text-gray-100">{simplified_formula}</code></pre>
                    <p class="mt-2 text-sm text-yellow-800 dark:text-yellow-200">
                        Still waiting for values: {', '.join(unresolved_names)}
                    </p>
                </div>
            """
        else:
            # Try to evaluate using the Python evaluator engine
            try:
                result = evaluate_formula(simplified_formula)
                result_html = f"""
                    <div class="mt-4 p-4 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg">
                        <h4 class="font-semibold mb-2 text-green-900 dark:text-green-100">Result:</h4>
                        <div class="text-2xl font-bold text-green-700 dark:text-green-300 mb-3">
                            {result}
                        </div>
                        <details class="text-sm">
                            <summary class="cursor-pointer text-green-800 dark:text-green-200 hover:text-green-600 dark:hover:text-green-400">
                                Show evaluated formula
                            </summary>
                            <pre class="mt-2 bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-600 overflow-x-auto"><code class="text-gray-900 dark:text-gray-100">{simplified_formula}</code></pre>
                        </details>
                    </div>
                """
            except FormulaEvaluationError as eval_error:
                result_html = f"""
                    <div class="mt-4 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg">
                        <h4 class="font-semibold mb-2 text-red-900 dark:text-red-100">Evaluation Error:</h4>
                        <p class="text-red-800 dark:text-red-200 mb-2">{str(eval_error)}</p>
                        <details class="text-sm">
                            <summary class="cursor-pointer text-red-800 dark:text-red-200">
                                Show formula
                            </summary>
                            <pre class="mt-2 bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-600 overflow-x-auto"><code class="text-gray-900 dark:text-gray-100">{simplified_formula}</code></pre>
                        </details>
                    </div>
                """
            except Exception as eval_error:
                result_html = f"""
                    <div class="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg">
                        <h4 class="font-semibold mb-2 text-yellow-900 dark:text-yellow-100">Simplified Formula:</h4>
                        <pre class="text-sm bg-white dark:bg-gray-800 p-3 rounded border border-gray-200 dark:border-gray-600 overflow-x-auto"><code class="text-gray-900 dark:text-gray-100">{simplified_formula}</code></pre>
                        <p class="mt-2 text-sm text-yellow-800 dark:text-yellow-200">
                            Note: Could not fully evaluate - {str(eval_error)}
                        </p>
                    </div>
                """
        
        # Write result to the separate output container
        eval_output_div = document.getElementById("eval-output")
        if eval_output_div:
            eval_output_div.innerHTML = result_html
        else:
            # Fallback: append to result_div if output div doesn't exist
            result_div = document.getElementById("eval-result")
            result_div.innerHTML += result_html
        
    except Exception as e:
        import traceback
        print("Error evaluating formula:", traceback.format_exc())


def initialize():
    """Initialize the Formula Evaluator tab"""
    print("=== Initializing Formula Evaluator ===")
    
    # Export functions to JavaScript
    window.loadFieldDependencies = load_field_dependencies
    window.evaluateFormulaWithValues = evaluate_formula_with_values
    window.convertEvaluatorFormulaDisplay = convert_evaluator_formula_display
    
    print("Formula Evaluator initialized successfully")


def convert_evaluator_formula_display(formula: str, output_format: str) -> str:
    """Convert a formula's field references to the specified format for display.
    
    Args:
        formula: The formula string to convert
        output_format: "field_ids" or "field_names"
    
    Returns:
        The formula with converted field references
    """
    try:
        metadata = get_local_storage_metadata()
        if not metadata:
            return formula
        
        converted = _convert_field_references(formula, metadata, output_format)
        return converted
    except Exception as e:
        print(f"Error converting formula display: {e}")
        return formula
