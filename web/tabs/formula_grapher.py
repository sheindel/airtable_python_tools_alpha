"""Formula Grapher Tab - Visualize formula logic as flowcharts"""
from pyscript import document, window
from pyodide.ffi.wrappers import add_event_listener
from typing import Optional, Dict, List, Set
import re

import sys
sys.path.append("web")
from components.airtable_client import (
    get_local_storage_metadata, 
    save_local_storage,
    find_field_by_id
)
from at_formula_parser import tokenize, FormulaTokenNode


# Counter for generating unique node IDs
_node_counter = 0


def _get_next_node_id() -> str:
    """Generate a unique node ID for Mermaid"""
    global _node_counter
    _node_counter += 1
    return f"n{_node_counter}"


def _reset_node_counter():
    """Reset the node counter for a new graph"""
    global _node_counter
    _node_counter = 0


def _escape_mermaid_text(text: str) -> str:
    """Escape special characters for Mermaid labels"""
    # Replace characters that could break Mermaid syntax
    text = text.replace('"', "'")
    text = text.replace('\n', ' ')
    text = text.replace('\r', '')
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    # Escape # to prevent it from being treated as a comment
    text = text.replace('#', '#35;') # for some reason this works as the mermaid replacement
    # Truncate very long text
    if len(text) > 50:
        text = text[:47] + "..."
    return text


def _get_field_name(field_id: str, metadata: dict) -> str:
    """Get field name from field ID"""
    field = find_field_by_id(metadata, field_id)
    if field:
        return field.get("name", field_id)
    return field_id


def _is_formula_field(field_id: str, metadata: dict) -> bool:
    """Check if a field is a formula field"""
    field = find_field_by_id(metadata, field_id)
    if field:
        return field.get("type") == "formula"
    return False


def _get_field_formula(field_id: str, metadata: dict) -> Optional[str]:
    """Get the formula for a formula field"""
    field = find_field_by_id(metadata, field_id)
    if field and field.get("type") == "formula":
        return field.get("options", {}).get("formula")
    return None


class MermaidFlowchartBuilder:
    """Builds a Mermaid flowchart from a formula token tree"""
    
    def __init__(
        self, 
        metadata: dict, 
        expand_fields: bool = False,
        max_expansion_depth: int = 1,
        use_field_names: bool = True
    ):
        self.metadata = metadata
        self.expand_fields = expand_fields
        self.max_expansion_depth = max_expansion_depth
        self.use_field_names = use_field_names
        self.nodes: List[str] = []
        self.edges: List[str] = []
        self.subgraphs: Dict[str, List[str]] = {}  # field_id -> [node lines]
        self.processed_fields: Set[str] = set()  # Track expanded fields
        _reset_node_counter()
    
    def _split_arguments(self, children: List[FormulaTokenNode]) -> List[List[FormulaTokenNode]]:
        """Split function children into argument groups by top-level commas.
        
        The key insight is that function calls have their opening paren as a child,
        so we need to count those to know when a closing paren belongs to a nested
        function vs being a top-level paren.
        """
        args: List[List[FormulaTokenNode]] = []
        current_arg: List[FormulaTokenNode] = []
        paren_depth = 0
        
        # The children include the opening ( of the function itself - skip it
        start_idx = 0
        end_idx = len(children)
        
        # Skip the function's opening paren
        if children and children[0].token_type == "OPERATOR" and children[0].value == "(":
            start_idx = 1
        
        for i in range(start_idx, end_idx):
            child = children[i]
            
            if child.token_type == "WHITESPACE":
                continue
            
            # Track if this is a function that has its own paren
            # Functions have their opening paren as a child
            if child.token_type == "FUNCTION_NAME" and child.children:
                # Check if any child is an opening paren
                has_paren = any(c.token_type == "OPERATOR" and c.value == "(" for c in child.children)
                if has_paren:
                    # This function "owns" the next closing paren we see
                    paren_depth += 1
                    current_arg.append(child)
                    continue
            
            if child.token_type == "OPERATOR":
                if child.value == "(":
                    # This is an orphan open paren (not attached to a function)
                    paren_depth += 1
                    current_arg.append(child)
                elif child.value == ")":
                    if paren_depth > 0:
                        paren_depth -= 1
                        current_arg.append(child)
                    else:
                        # This is the closing paren of the function we're analyzing
                        break
                elif child.value == "," and paren_depth == 0:
                    # Top-level comma - split arguments here
                    if current_arg:
                        args.append(current_arg)
                    current_arg = []
                else:
                    current_arg.append(child)
            else:
                current_arg.append(child)
        
        # Add the last argument
        if current_arg:
            args.append(current_arg)
        
        return args
    
    def _process_expression(self, tokens: List[FormulaTokenNode], depth: int) -> Optional[str]:
        """Process a list of tokens that form an expression.
        
        This handles expressions like:
        - Single values: {Field}, "string", 123
        - Comparisons: {Field}=BLANK(), FIND(...)>0
        - Complex: AND({A}, {B})
        """
        if not tokens:
            return None
        
        # Single token - process directly
        if len(tokens) == 1:
            return self._process_node(tokens[0], depth)
        
        # Multiple tokens - look for comparison operators to create a comparison node
        # Find the main operator (=, >, <, >=, <=, !=, &)
        comparison_ops = ["=", ">", "<", ">=", "<=", "!="]
        
        for i, token in enumerate(tokens):
            if token.token_type == "OPERATOR" and token.value in comparison_ops:
                # Found a comparison operator - create a comparison node
                left_tokens = tokens[:i]
                right_tokens = tokens[i+1:]
                
                node_id = _get_next_node_id()
                self.nodes.append(f'{node_id}["{token.value}"]')
                
                # Process left side
                if left_tokens:
                    left_id = self._process_expression(left_tokens, depth + 1)
                    if left_id:
                        self.edges.append(f"{left_id} --> {node_id}")
                
                # Process right side
                if right_tokens:
                    right_id = self._process_expression(right_tokens, depth + 1)
                    if right_id:
                        self.edges.append(f"{right_id} --> {node_id}")
                
                return node_id
        
        # Check for concatenation operator &
        for i, token in enumerate(tokens):
            if token.token_type == "OPERATOR" and token.value == "&":
                node_id = _get_next_node_id()
                self.nodes.append(f'{node_id}(["&"])')
                
                left_tokens = tokens[:i]
                right_tokens = tokens[i+1:]
                
                if left_tokens:
                    left_id = self._process_expression(left_tokens, depth + 1)
                    if left_id:
                        self.edges.append(f"{left_id} --> {node_id}")
                
                if right_tokens:
                    right_id = self._process_expression(right_tokens, depth + 1)
                    if right_id:
                        self.edges.append(f"{right_id} --> {node_id}")
                
                return node_id
        
        # Check for math operators +, -, *, /
        math_ops = ["+", "-", "*", "/"]
        for i, token in enumerate(tokens):
            if token.token_type == "OPERATOR" and token.value in math_ops:
                node_id = _get_next_node_id()
                self.nodes.append(f'{node_id}["{token.value}"]')
                
                left_tokens = tokens[:i]
                right_tokens = tokens[i+1:]
                
                if left_tokens:
                    left_id = self._process_expression(left_tokens, depth + 1)
                    if left_id:
                        self.edges.append(f"{left_id} --> {node_id}")
                
                if right_tokens:
                    right_id = self._process_expression(right_tokens, depth + 1)
                    if right_id:
                        self.edges.append(f"{right_id} --> {node_id}")
                
                return node_id
        
        # No operator found - just process the first significant token
        # This handles cases like a function call with no operators
        for token in tokens:
            if token.token_type not in ("OPERATOR", "WHITESPACE"):
                return self._process_node(token, depth)
        
        return None
    
    def build(self, formula: str, root_field_id: Optional[str] = None) -> str:
        """Build a Mermaid flowchart from a formula string"""
        root_node, tokens = tokenize(formula)
        
        # Create the root node for the formula result
        result_id = _get_next_node_id()
        if root_field_id:
            field_name = _get_field_name(root_field_id, self.metadata)
            self.nodes.append(f'{result_id}[["🎯 {_escape_mermaid_text(field_name)}"]]')
        else:
            self.nodes.append(f'{result_id}[["🎯 Result"]]')
        
        # Process the token tree
        if root_node.children:
            child_id = self._process_node(root_node.children[0], depth=0)
            if child_id:
                self.edges.append(f"{child_id} --> {result_id}")
        
        return self._generate_mermaid()
    
    def _process_node(self, node: FormulaTokenNode, depth: int = 0) -> Optional[str]:
        """Process a token node and return its Mermaid node ID"""
        
        if node.token_type == "FUNCTION_NAME":
            return self._process_function(node, depth)
        elif node.token_type == "FIELD_ID":
            return self._process_field_reference(node, depth)
        elif node.token_type == "STRING_LITERAL":
            node_id = _get_next_node_id()
            self.nodes.append(f'{node_id}["{_escape_mermaid_text(node.value)}"]')
            return node_id
        elif node.token_type == "NUMBER":
            node_id = _get_next_node_id()
            self.nodes.append(f'{node_id}["{node.value}"]')
            return node_id
        elif node.token_type == "BOOLEAN":
            node_id = _get_next_node_id()
            self.nodes.append(f'{node_id}["{node.value}"]')
            return node_id
        elif node.token_type == "OPERATOR":
            # Operators are now handled by _process_expression
            # This case handles standalone operators (rare)
            return None
        elif node.token_type == "ROOT":
            # Process all children of ROOT
            last_id = None
            for child in node.children:
                last_id = self._process_node(child, depth)
            return last_id
        
        return None
    
    def _process_function(self, node: FormulaTokenNode, depth: int) -> Optional[str]:
        """Process a function call node"""
        func_name = node.value.upper()
        
        # Special handling for different function types
        if func_name == "IF":
            return self._process_if_function(node, depth)
        elif func_name == "SWITCH":
            return self._process_switch_function(node, depth)
        elif func_name in ("AND", "OR"):
            return self._process_logic_function(node, depth)
        elif func_name == "CONCATENATE":
            return self._process_concatenate_function(node, depth)
        elif func_name == "NOT":
            return self._process_not_function(node, depth)
        else:
            return self._process_generic_function(node, depth)
    
    def _process_if_function(self, node: FormulaTokenNode, depth: int) -> Optional[str]:
        """Process IF(condition, true_result, false_result) as a decision diamond"""
        node_id = _get_next_node_id()
        
        # Create diamond node for IF
        self.nodes.append(f'{node_id}{{"IF"}}')
        
        # Split children into argument groups by commas
        arg_groups = self._split_arguments(node.children)
        
        # Process condition (first argument group)
        if len(arg_groups) > 0:
            cond_id = self._process_expression(arg_groups[0], depth + 1)
            if cond_id:
                self.edges.append(f"{cond_id} -->|condition| {node_id}")
        
        # Process true branch (second argument group)
        if len(arg_groups) > 1:
            true_id = self._process_expression(arg_groups[1], depth + 1)
            if true_id:
                self.edges.append(f"{node_id} -->|TRUE| {true_id}")
        
        # Process false branch (third argument group)
        if len(arg_groups) > 2:
            false_id = self._process_expression(arg_groups[2], depth + 1)
            if false_id:
                self.edges.append(f"{node_id} -->|FALSE| {false_id}")
        
        return node_id
    
    def _process_switch_function(self, node: FormulaTokenNode, depth: int) -> Optional[str]:
        """Process SWITCH(expr, case1, val1, case2, val2, ..., default) as stacked decisions"""
        # Split children into argument groups
        arg_groups = self._split_arguments(node.children)
        
        if len(arg_groups) < 2:
            return self._process_generic_function(node, depth)
        
        # Create main SWITCH node
        switch_id = _get_next_node_id()
        self.nodes.append(f'{switch_id}{{"SWITCH"}}')
        
        # Process the expression being switched on (first argument)
        expr_id = self._process_expression(arg_groups[0], depth + 1)
        if expr_id:
            self.edges.append(f"{expr_id} -->|value| {switch_id}")
        
        # Process case/value pairs (arguments 1,2 then 3,4 then 5,6 etc.)
        i = 1
        while i < len(arg_groups) - 1:
            case_group = arg_groups[i]
            value_group = arg_groups[i + 1] if i + 1 < len(arg_groups) else None
            
            if value_group:
                # Get case label from the first token in case group
                case_label = "case"
                if case_group and case_group[0].value:
                    case_label = _escape_mermaid_text(case_group[0].value)
                
                value_id = self._process_expression(value_group, depth + 1)
                if value_id:
                    self.edges.append(f'{switch_id} -->|"{case_label}"| {value_id}')
            
            i += 2
        
        # Handle default case (odd number of remaining args means there's a default)
        remaining_args = len(arg_groups) - 1  # Exclude expression
        if remaining_args % 2 == 1 and len(arg_groups) > 2:
            default_id = self._process_expression(arg_groups[-1], depth + 1)
            if default_id:
                self.edges.append(f'{switch_id} -->|default| {default_id}')
        
        return switch_id
    
    def _process_logic_function(self, node: FormulaTokenNode, depth: int) -> Optional[str]:
        """Process AND/OR as logic gate nodes"""
        node_id = _get_next_node_id()
        func_name = node.value.upper()
        
        # Use parallelogram shape for logic gates
        self.nodes.append(f'{node_id}[/{func_name}/]')
        
        # Split children into argument groups
        arg_groups = self._split_arguments(node.children)
        
        # Connect all inputs
        for arg_group in arg_groups:
            arg_id = self._process_expression(arg_group, depth + 1)
            if arg_id:
                self.edges.append(f"{arg_id} --> {node_id}")
        
        return node_id
    
    def _process_concatenate_function(self, node: FormulaTokenNode, depth: int) -> Optional[str]:
        """Process CONCATENATE as a merge block with multiple inputs"""
        node_id = _get_next_node_id()
        
        # Use stadium shape for concatenate
        self.nodes.append(f'{node_id}(["CONCATENATE"])')
        
        # Split children into argument groups
        arg_groups = self._split_arguments(node.children)
        
        # Connect all inputs in order
        for i, arg_group in enumerate(arg_groups):
            arg_id = self._process_expression(arg_group, depth + 1)
            if arg_id:
                self.edges.append(f"{arg_id} -->|{i+1}| {node_id}")
        
        return node_id
    
    def _process_not_function(self, node: FormulaTokenNode, depth: int) -> Optional[str]:
        """Process NOT as an inverter"""
        node_id = _get_next_node_id()
        
        self.nodes.append(f'{node_id}[/"NOT"/]')
        
        # Split children into argument groups
        arg_groups = self._split_arguments(node.children)
        
        if arg_groups:
            arg_id = self._process_expression(arg_groups[0], depth + 1)
            if arg_id:
                self.edges.append(f"{arg_id} --> {node_id}")
        
        return node_id
    
    def _process_generic_function(self, node: FormulaTokenNode, depth: int) -> Optional[str]:
        """Process a generic function call"""
        node_id = _get_next_node_id()
        func_name = node.value.upper()
        
        # Use rounded rectangle for generic functions
        self.nodes.append(f'{node_id}("{func_name}")')
        
        # Split children into argument groups
        arg_groups = self._split_arguments(node.children)
        
        # Connect arguments
        for arg_group in arg_groups:
            arg_id = self._process_expression(arg_group, depth + 1)
            if arg_id:
                self.edges.append(f"{arg_id} --> {node_id}")
        
        return node_id
    
    def _process_field_reference(self, node: FormulaTokenNode, depth: int) -> Optional[str]:
        """Process a field reference"""
        field_id = node.value
        field_name = _get_field_name(field_id, self.metadata) if self.use_field_names else field_id
        
        # Check if this is a formula field that should be expanded
        if (self.expand_fields and 
            depth < self.max_expansion_depth and 
            field_id not in self.processed_fields and
            _is_formula_field(field_id, self.metadata)):
            
            # Mark as processed to avoid circular references
            self.processed_fields.add(field_id)
            
            # Get the formula and create a subgraph
            formula = _get_field_formula(field_id, self.metadata)
            if formula:
                return self._create_field_subgraph(field_id, field_name, formula, depth)
        
        # Create a simple field reference node
        node_id = _get_next_node_id()
        
        # Use different styling for formula fields vs regular fields
        if _is_formula_field(field_id, self.metadata):
            self.nodes.append(f'{node_id}[["🖩 {_escape_mermaid_text(field_name)}"]]')
        else:
            self.nodes.append(f'{node_id}[("📊 {_escape_mermaid_text(field_name)}")]')
        
        return node_id
    
    def _create_field_subgraph(
        self, 
        field_id: str, 
        field_name: str, 
        formula: str, 
        depth: int
    ) -> Optional[str]:
        """Create a subgraph for an expanded formula field"""
        # Parse and process the nested formula
        root_node, _ = tokenize(formula)
        
        # Create a result node for this subgraph
        result_id = _get_next_node_id()
        self.nodes.append(f'{result_id}[["🖩 {_escape_mermaid_text(field_name)}"]]')
        
        # Process the formula tree
        if root_node.children:
            child_id = self._process_node(root_node.children[0], depth + 1)
            if child_id:
                self.edges.append(f"{child_id} --> {result_id}")
        
        return result_id
    
    def _generate_mermaid(self) -> str:
        """Generate the final Mermaid flowchart code"""
        lines = ["flowchart TD"]
        
        # Add all nodes
        for node in self.nodes:
            lines.append(f"    {node}")
        
        # Add all edges
        for edge in self.edges:
            lines.append(f"    {edge}")
        
        return "\n".join(lines)


def generate_formula_flowchart(
    table_name: str,
    field_name: str,
    expand_fields: bool = False,
    max_expansion_depth: int = 1,
    use_field_names: bool = True,
    flowchart_direction: str = "TD"
) -> str:
    """
    Generate a Mermaid flowchart for a formula field.
    
    Args:
        table_name: Name of the table containing the field
        field_name: Name of the formula field
        expand_fields: Whether to expand referenced formula fields
        max_expansion_depth: Maximum depth for field expansion
        use_field_names: Use field names instead of IDs
        flowchart_direction: Mermaid direction (TD, LR, RL, BT)
    
    Returns:
        Mermaid flowchart definition string
    """
    metadata = get_local_storage_metadata()
    if not metadata:
        raise ValueError("No metadata available")
    
    # Find the table and field
    table = None
    field = None
    for t in metadata.get("tables", []):
        if t["name"] == table_name:
            table = t
            for f in t.get("fields", []):
                if f["name"] == field_name:
                    field = f
                    break
            break
    
    if not table:
        raise ValueError(f"Table '{table_name}' not found")
    if not field:
        raise ValueError(f"Field '{field_name}' not found in table '{table_name}'")
    if field.get("type") != "formula":
        raise ValueError(f"Field '{field_name}' is not a formula field")
    
    formula = field.get("options", {}).get("formula", "")
    if not formula:
        raise ValueError(f"Field '{field_name}' has no formula")
    
    # Build the flowchart
    builder = MermaidFlowchartBuilder(
        metadata=metadata,
        expand_fields=expand_fields,
        max_expansion_depth=max_expansion_depth,
        use_field_names=use_field_names
    )
    
    mermaid_code = builder.build(formula, field.get("id"))
    
    # Replace direction if not TD
    if flowchart_direction != "TD":
        mermaid_code = mermaid_code.replace("flowchart TD", f"flowchart {flowchart_direction}")
    
    return mermaid_code


def graph_formula_from_ui(
    table_name: str,
    field_name: str,
    expand_fields: bool,
    max_expansion_depth: Optional[int],
    flowchart_direction: str
):
    """
    UI handler for generating formula flowchart. Called from JavaScript.
    """
    try:
        depth = max_expansion_depth if max_expansion_depth is not None else 1
        
        mermaid_code = generate_formula_flowchart(
            table_name=table_name,
            field_name=field_name,
            expand_fields=expand_fields,
            max_expansion_depth=depth,
            use_field_names=True,
            flowchart_direction=flowchart_direction
        )
        
        # Store for copy/download functions
        save_local_storage("lastFormulaGraphDefinition", mermaid_code)
        
        # Update the UI
        mermaid_container = document.getElementById("formula-grapher-mermaid-container")
        mermaid_container.innerHTML = f'<div class="mermaid">{mermaid_code}</div>'
        window.mermaid.run()
        
        print(f"Successfully generated flowchart for {table_name}.{field_name}")
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        
        mermaid_container = document.getElementById("formula-grapher-mermaid-container")
        mermaid_container.innerHTML = f'<span class="text-red-600 dark:text-red-400">{error_msg}</span>'


def get_formula_for_display(table_name: str, field_name: str) -> str:
    """Get a formula's text for display in the UI"""
    metadata = get_local_storage_metadata()
    if not metadata:
        return ""
    
    for table in metadata.get("tables", []):
        if table["name"] == table_name:
            for field in table.get("fields", []):
                if field["name"] == field_name and field.get("type") == "formula":
                    formula = field.get("options", {}).get("formula", "")
                    # Convert field IDs to names for display
                    field_id_pattern = r'\{(fld[a-zA-Z0-9]+)\}'
                    
                    def replace_with_name(match):
                        fld_id = match.group(1)
                        fld = find_field_by_id(metadata, fld_id)
                        if fld:
                            return f"{{{fld['name']}}}"
                        return match.group(0)
                    
                    return re.sub(field_id_pattern, replace_with_name, formula)
    
    return ""


def parameters_changed(event):
    """Handle parameter changes from UI controls"""
    try:
        table_dropdown = document.getElementById("grapher-table-dropdown")
        field_dropdown = document.getElementById("grapher-field-dropdown")
        
        if not table_dropdown or not field_dropdown:
            print("Error: Required UI elements not found")
            return
        
        table_name = table_dropdown.value.strip()
        field_name = field_dropdown.value.strip()
        
        if not table_name or not field_name:
            return
        
        # Get other options
        expand_checkbox = document.getElementById("grapher-expand-fields")
        depth_input = document.getElementById("grapher-expansion-depth")
        direction_dropdown = document.getElementById("grapher-flowchart-direction")
        
        expand_fields = expand_checkbox.checked if expand_checkbox else False
        direction = direction_dropdown.value if direction_dropdown else "TD"
        
        depth_value = depth_input.value.strip() if depth_input else ""
        max_depth = int(depth_value) if depth_value else 1
        
        # Generate the flowchart
        graph_formula_from_ui(table_name, field_name, expand_fields, max_depth, direction)
        
    except Exception as e:
        error_msg = f"Error in parameters_changed: {str(e)}"
        print(error_msg)
        mermaid_container = document.getElementById("formula-grapher-mermaid-container")
        if mermaid_container:
            mermaid_container.innerHTML = f'<span class="text-red-600 dark:text-red-400">{error_msg}</span>'


def initialize():
    """Initialize the Formula Grapher tab"""
    print("Formula Grapher tab initialized")
    
    # Export functions to JavaScript
    window.graphFormulaFromUI = graph_formula_from_ui
    window.getFormulaForDisplay = get_formula_for_display
    
    # Set up event listeners
    field_dropdown = document.getElementById("grapher-field-dropdown")
    direction_dropdown = document.getElementById("grapher-flowchart-direction")
    expand_checkbox = document.getElementById("grapher-expand-fields")
    depth_input = document.getElementById("grapher-expansion-depth")
    
    if field_dropdown:
        add_event_listener(field_dropdown, "change", parameters_changed)
    if direction_dropdown:
        add_event_listener(direction_dropdown, "change", parameters_changed)
    if expand_checkbox:
        add_event_listener(expand_checkbox, "change", parameters_changed)
    if depth_input:
        add_event_listener(depth_input, "input", parameters_changed)
