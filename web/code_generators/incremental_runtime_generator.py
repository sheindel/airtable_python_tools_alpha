"""
Incremental Runtime Generator - Generate efficient formula evaluators

This module generates Python code for evaluating Airtable formulas with
incremental computation. Only recalculates formulas when their dependencies
actually change, using a depth-based computation graph.

Key Features:
- Dependency-aware recomputation
- Multiple data access patterns (dataclass, dict, pydantic)
- Configurable null safety checks
- Supports formula, lookup, rollup, and count fields
"""

import sys
sys.path.append("web")

from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
import networkx as nx

from at_metadata_graph import (
    metadata_to_graph,
    get_computation_order_with_metadata,
    get_formula_depth,
)
from at_types import AirtableMetadata, AirTableFieldMetadata
from constants import (
    FIELD_TYPE_FORMULA,
    FIELD_TYPE_ROLLUP,
    FIELD_TYPE_LOOKUP,
    FIELD_TYPE_COUNT,
    COMPUTED_FIELD_TYPES,
)


@dataclass
class GeneratorOptions:
    """Configuration options for code generation"""
    data_access_mode: str = "dataclass"  # "dataclass" | "dict" | "pydantic"
    include_null_checks: bool = True
    include_type_hints: bool = True
    include_docstrings: bool = True
    include_examples: bool = False
    optimize_depth_skipping: bool = True
    track_computation_stats: bool = False
    output_format: str = "single_file"  # "single_file" | "module"
    include_tests: bool = False


@dataclass
class FieldInfo:
    """Information about a field in the computation graph"""
    field_id: str
    name: str
    field_type: str
    table_id: str
    table_name: str
    depth: int
    dependencies: List[str]  # Field IDs this field depends on
    dependents: List[str]    # Field IDs that depend on this field
    function_name: Optional[str] = None  # Name of compute function (for computed fields)
    metadata: Optional[Dict] = None  # Full field metadata from Airtable


@dataclass
class ComputationGraph:
    """
    Computation graph with fields organized by depth.
    
    This structure enables efficient incremental computation by:
    1. Processing fields in depth order (dependencies before dependents)
    2. Tracking which fields need recomputation
    3. Avoiding duplicate work within a computation cycle
    """
    max_depth: int
    depths: Dict[int, Dict[str, FieldInfo]]  # depth -> field_id -> FieldInfo
    field_id_to_name: Dict[str, str]
    field_name_to_id: Dict[str, str]
    table_fields: Dict[str, List[str]]  # table_id -> list of field names
    
    def get_field(self, field_id: str) -> Optional[FieldInfo]:
        """Get field info by ID"""
        for depth_fields in self.depths.values():
            if field_id in depth_fields:
                return depth_fields[field_id]
        return None
    
    def get_fields_at_depth(self, depth: int) -> Dict[str, FieldInfo]:
        """Get all fields at a specific depth"""
        return self.depths.get(depth, {})
    
    def get_computed_fields(self) -> List[FieldInfo]:
        """Get all computed fields (formula, rollup, lookup, count)"""
        computed = []
        for depth_fields in self.depths.values():
            for field_info in depth_fields.values():
                if field_info.field_type in COMPUTED_FIELD_TYPES:
                    computed.append(field_info)
        return computed


def build_computation_graph(
    metadata: AirtableMetadata,
    table_id: Optional[str] = None
) -> ComputationGraph:
    """
    Build a computation graph from Airtable metadata.
    
    The graph organizes fields by dependency depth, enabling efficient
    incremental computation. Fields with no dependencies are at depth 0,
    fields that depend only on depth-0 fields are at depth 1, etc.
    
    Args:
        metadata: Airtable metadata dict
        table_id: Optional - limit to a single table
    
    Returns:
        ComputationGraph with all necessary information for code generation
    """
    # Build NetworkX graph
    G = metadata_to_graph(metadata)
    
    # Get fields organized by computation depth
    depth_groups = get_computation_order_with_metadata(metadata)
    
    # Build the computation graph structure
    depths: Dict[int, Dict[str, FieldInfo]] = {}
    field_id_to_name: Dict[str, str] = {}
    field_name_to_id: Dict[str, str] = {}
    table_fields: Dict[str, List[str]] = {}
    
    # Process each depth level
    for depth, fields_at_depth in enumerate(depth_groups):
        depths[depth] = {}
        
        for field_info_dict in fields_at_depth:
            field_id = field_info_dict["id"]
            field_name = field_info_dict["name"]
            field_type = field_info_dict["type"]
            table_name = field_info_dict["table_name"]
            
            # Filter by table if requested  
            # Need to find table_id from table_name since field_info_dict doesn't include it
            if table_id:
                # Find the table_id for this field's table_name
                field_table_id = None
                for table in metadata.get("tables", []):
                    if table["name"] == table_name:
                        field_table_id = table["id"]
                        break
                
                if field_table_id != table_id:
                    continue
            
            # Get dependencies (predecessors in graph)
            dependencies = []
            if field_id in G.nodes:
                for pred in G.predecessors(field_id):
                    # Skip table nodes
                    if G.nodes[pred].get("type") == "field":
                        dependencies.append(pred)
            
            # Get dependents (successors in graph)
            dependents = []
            if field_id in G.nodes:
                for succ in G.successors(field_id):
                    # Skip table nodes
                    if G.nodes[succ].get("type") == "field":
                        dependents.append(succ)
            
            # Get full field metadata
            field_metadata = None
            if field_id in G.nodes:
                field_metadata = G.nodes[field_id].get("metadata")
            
            # Determine function name for computed fields
            function_name = None
            if field_type in COMPUTED_FIELD_TYPES:
                # Convert field name to valid Python identifier
                function_name = f"compute_{_to_snake_case(field_name)}"
            
            # Create FieldInfo
            field_info = FieldInfo(
                field_id=field_id,
                name=field_name,
                field_type=field_type,
                table_id=field_info_dict.get("table_id", ""),
                table_name=table_name,
                depth=depth,
                dependencies=dependencies,
                dependents=dependents,
                function_name=function_name,
                metadata=field_metadata
            )
            
            # Add to depths dict
            depths[depth][field_id] = field_info
            
            # Add to lookup dicts
            field_id_to_name[field_id] = field_name
            field_name_to_id[field_name] = field_id
            
            # Track fields by table
            table_id_key = field_info_dict.get("table_id", "")
            if table_id_key:
                if table_id_key not in table_fields:
                    table_fields[table_id_key] = []
                table_fields[table_id_key].append(field_name)
    
    max_depth = len(depth_groups) - 1
    
    return ComputationGraph(
        max_depth=max_depth,
        depths=depths,
        field_id_to_name=field_id_to_name,
        field_name_to_id=field_name_to_id,
        table_fields=table_fields
    )


def generate_computation_context_class(
    graph: ComputationGraph,
    options: GeneratorOptions
) -> str:
    """
    Generate the ComputationContext class.
    
    This class provides access to related records for lookups/rollups
    and tracks which fields have been computed in the current cycle.
    
    Args:
        graph: Computation graph
        options: Generator options
    
    Returns:
        Python code string for the ComputationContext class
    """
    parts = []
    
    # Class definition
    parts.append("class ComputationContext:")
    
    # Docstring
    if options.include_docstrings:
        parts.append('    """')
        parts.append("    Context object passed to all formula functions.")
        parts.append("    Provides access to related records for lookups/rollups.")
        parts.append('    """')
    
    # __init__ method
    if options.include_type_hints:
        parts.append("    def __init__(self, record: Any, all_records: Dict[str, List[Any]]):")
    else:
        parts.append("    def __init__(self, record, all_records):")
    
    if options.include_docstrings:
        parts.append('        """')
        parts.append("        Initialize computation context.")
        parts.append("        ")
        parts.append("        Args:")
        parts.append("            record: The record being computed")
        parts.append("            all_records: Dict of table_id -> list of records for lookups")
        parts.append('        """')
    
    parts.append("        self.record = record")
    parts.append("        self.all_records = all_records")
    parts.append("        self.computed_this_cycle = set()  # Track computed field IDs")
    parts.append("")
    
    # get_linked_records method
    if options.include_type_hints:
        parts.append("    def get_linked_records(self, field_name: str, target_table_id: str) -> List[Any]:")
    else:
        parts.append("    def get_linked_records(self, field_name, target_table_id):")
    
    if options.include_docstrings:
        parts.append('        """Get records linked via a multipleRecordLinks field."""')
    
    parts.append("        # Get linked record IDs from the field")
    parts.append("        if hasattr(self.record, field_name):")
    parts.append("            linked_ids = getattr(self.record, field_name, [])")
    parts.append("        else:")
    parts.append("            linked_ids = self.record.get(field_name, [])")
    parts.append("        ")
    parts.append("        if not linked_ids:")
    parts.append("            return []")
    parts.append("        ")
    parts.append("        # Get records from the linked table")
    parts.append("        target_records = self.all_records.get(target_table_id, [])")
    parts.append("        ")
    parts.append("        # Filter to only linked records")
    parts.append("        result = []")
    parts.append("        for record in target_records:")
    parts.append("            record_id = record.id if hasattr(record, 'id') else record.get('id')")
    parts.append("            if record_id in linked_ids:")
    parts.append("                result.append(record)")
    parts.append("        ")
    parts.append("        return result")
    parts.append("")
    
    # lookup method
    if options.include_type_hints:
        parts.append("    def lookup(self, link_field: str, target_field: str, target_table_id: str = None) -> List[Any]:")
    else:
        parts.append("    def lookup(self, link_field, target_field, target_table_id=None):")
    
    if options.include_docstrings:
        parts.append('        """Perform a lookup operation."""')
    
    parts.append("        if not target_table_id:")
    parts.append("            # Try to infer from LINKED_TABLE_MAP if available")
    parts.append("            target_table_id = LINKED_TABLE_MAP.get(link_field, '')")
    parts.append("        ")
    parts.append("        linked_records = self.get_linked_records(link_field, target_table_id)")
    parts.append("        ")
    parts.append("        # Extract target field values")
    parts.append("        result = []")
    parts.append("        for record in linked_records:")
    parts.append("            if hasattr(record, target_field):")
    parts.append("                value = getattr(record, target_field)")
    parts.append("            else:")
    parts.append("                value = record.get(target_field)")
    parts.append("            result.append(value)")
    parts.append("        ")
    parts.append("        return result")
    parts.append("")
    
    # rollup method
    if options.include_type_hints:
        parts.append("    def rollup(self, link_field: str, target_field: str, aggregation: str, target_table_id: str = None) -> Any:")
    else:
        parts.append("    def rollup(self, link_field, target_field, aggregation, target_table_id=None):")
    
    if options.include_docstrings:
        parts.append('        """Perform a rollup aggregation."""')
    
    parts.append("        values = self.lookup(link_field, target_field, target_table_id)")
    parts.append("        ")
    parts.append("        # Filter out None values for numeric aggregations")
    parts.append("        if aggregation in ['SUM', 'AVG', 'MAX', 'MIN']:")
    parts.append("            values = [v for v in values if v is not None]")
    parts.append("        ")
    parts.append("        if aggregation == 'SUM':")
    parts.append("            return sum(values) if values else 0")
    parts.append("        elif aggregation == 'AVG':")
    parts.append("            return sum(values) / len(values) if values else 0")
    parts.append("        elif aggregation == 'COUNT':")
    parts.append("            return len(values)")
    parts.append("        elif aggregation == 'MAX':")
    parts.append("            return max(values) if values else None")
    parts.append("        elif aggregation == 'MIN':")
    parts.append("            return min(values) if values else None")
    parts.append("        elif aggregation == 'AND':")
    parts.append("            return all(values) if values else True")
    parts.append("        elif aggregation == 'OR':")
    parts.append("            return any(values) if values else False")
    parts.append("        elif aggregation == 'CONCATENATE':")
    parts.append("            return ', '.join(str(v) for v in values if v is not None)")
    parts.append("        else:")
    parts.append("            # Unsupported aggregation")
    parts.append("            return None")
    
    return "\n".join(parts)


# ============================================================================
# Phase 2: Formula Function Generators
# ============================================================================

def generate_formula_function(
    field_info: FieldInfo,
    metadata: AirtableMetadata,
    options: GeneratorOptions
) -> str:
    """
    Generate a Python function for a formula field.
    
    Creates a standalone function that:
    - Takes record and context as parameters
    - Transpiles the Airtable formula to Python
    - Includes null safety checks (if enabled)
    - Returns the computed value
    
    Args:
        field_info: Field information from computation graph
        metadata: Full Airtable metadata
        options: Generator options
        
    Returns:
        Python function definition as string
        
    Example output:
        ```python
        def compute_full_name(record: Contact, context: ComputationContext) -> Optional[str]:
            \"\"\"
            Compute Full Name field
            Formula: {First Name} & " " & {Last Name}
            Dependencies: first_name, last_name
            \"\"\"
            # Null safety checks
            if record.first_name is None or record.last_name is None:
                return None
            
            # Generated formula code
            return str(record.first_name) + " " + str(record.last_name)
        ```
    """
    from code_generators.python_runtime_generator import PythonFormulaTranspiler
    from at_formula_parser import parse_airtable_formula
    
    # Get field metadata
    field_metadata = field_info.metadata
    if not field_metadata:
        return _generate_stub_function(field_info, "Formula metadata missing")
    
    options_dict = field_metadata.get("options", {})
    formula_str = options_dict.get("formula")
    
    if not formula_str:
        return _generate_stub_function(field_info, "Formula string missing")
    
    # Parse and transpile the formula
    try:
        ast = parse_airtable_formula(formula_str, metadata)
        transpiler = PythonFormulaTranspiler(
            data_access_mode=options.data_access_mode,
            include_null_checks=False  # We'll handle null checks separately
        )
        formula_code = transpiler.transpile(ast)
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {e}"
        # Uncomment for debugging: print(traceback.format_exc())
        return _generate_stub_function(field_info, f"Parse error: {error_detail}")
    
    # Generate function
    func_name = field_info.function_name or f"compute_{_to_snake_case(field_info.name)}"
    field_name_snake = _to_snake_case(field_info.name)
    
    # Build dependency list for docstring
    dep_names = []
    for dep_id in field_info.dependencies:
        dep_info = _find_field_info_by_id(metadata, dep_id)
        if dep_info:
            dep_names.append(_to_snake_case(dep_info["name"]))
    dep_list = ", ".join(dep_names) if dep_names else "none"
    
    # Generate null checks if enabled
    # NOTE: For formula fields, we DON'T add upfront null checks because the 
    # transpiled formula code already handles None values appropriately (e.g.,
    # string concatenation converts None to empty string). Adding a blanket 
    # null check would prevent the formula from running and return None even 
    # when the formula could produce a valid result.
    null_check_code = ""
    if options.include_null_checks and dep_names and field_info.field_type != FIELD_TYPE_FORMULA:
        checks = [f"record.{dep}" for dep in dep_names if options.data_access_mode != "dict"]
        if options.data_access_mode == "dict":
            checks = [f'record.get("{dep}")' for dep in dep_names]
        
        if checks:
            check_expr = " is None or ".join(checks) + " is None"
            null_check_code = f"""    # Null safety check
    if {check_expr}:
        return None
    
"""
    
    # Build function
    parts = []
    
    # Function signature
    if options.include_type_hints:
        parts.append(f"def {func_name}(record, context: 'ComputationContext') -> Optional[Any]:")
    else:
        parts.append(f"def {func_name}(record, context):")
    
    # Docstring
    if options.include_docstrings:
        parts.append(f'''    """
    Compute {field_info.name} field
    Formula: {formula_str}
    Dependencies: {dep_list}
    """''')
    
    # Null checks
    if null_check_code:
        parts.append(null_check_code)
    
    # Formula code
    parts.append(f"    return {formula_code}")
    
    return "\n".join(parts)


def generate_lookup_function(
    field_info: FieldInfo,
    metadata: AirtableMetadata,
    options: GeneratorOptions
) -> str:
    """
    Generate a Python function for a lookup field.
    
    Lookups retrieve values from linked records via a relationship field.
    
    Args:
        field_info: Field information from computation graph
        metadata: Full Airtable metadata
        options: Generator options
        
    Returns:
        Python function definition as string
        
    Example output:
        ```python
        def compute_company_name(record: Contact, context: ComputationContext) -> List[str]:
            \"\"\"
            Lookup Company Name via company link
            \"\"\"
            return context.lookup("company", "company_name")
        ```
    """
    field_metadata = field_info.metadata
    if not field_metadata:
        return _generate_stub_function(field_info, "Lookup metadata missing")
    
    options_dict = field_metadata.get("options", {})
    link_field_id = options_dict.get("recordLinkFieldId")
    target_field_id = options_dict.get("fieldIdInLinkedTable")
    
    if not link_field_id or not target_field_id:
        return _generate_stub_function(field_info, "Lookup configuration incomplete")
    
    # Find link field and target field names
    link_field = _find_field_info_by_id(metadata, link_field_id)
    target_field = _find_field_info_by_id(metadata, target_field_id)
    
    if not link_field or not target_field:
        return _generate_stub_function(field_info, "Linked fields not found")
    
    link_field_name = _to_snake_case(link_field["name"])
    target_field_name = _to_snake_case(target_field["name"])
    
    # Generate function
    func_name = field_info.function_name or f"compute_{_to_snake_case(field_info.name)}"
    
    # Generate null checks if enabled
    null_check_code = ""
    if options.include_null_checks:
        if options.data_access_mode == "dict":
            check_expr = f'record.get("{link_field_name}") is None'
        else:
            check_expr = f'record.{link_field_name} is None'
        
        null_check_code = f"""    # Null safety check
    if {check_expr}:
        return []
    
"""
    
    parts = []
    
    # Function signature
    if options.include_type_hints:
        parts.append(f"def {func_name}(record, context: 'ComputationContext') -> List[Any]:")
    else:
        parts.append(f"def {func_name}(record, context):")
    
    # Docstring
    if options.include_docstrings:
        parts.append(f'''    """
    Lookup {field_info.name} via {link_field["name"]}
    """''')
    
    # Null check
    if null_check_code:
        parts.append(null_check_code)
    
    # Lookup code
    parts.append(f'    return context.lookup("{link_field_name}", "{target_field_name}")')
    
    return "\n".join(parts)


def generate_rollup_function(
    field_info: FieldInfo,
    metadata: AirtableMetadata,
    options: GeneratorOptions
) -> str:
    """
    Generate a Python function for a rollup field.
    
    Rollups aggregate values from linked records using functions like SUM, COUNT, etc.
    
    Args:
        field_info: Field information from computation graph
        metadata: Full Airtable metadata
        options: Generator options
        
    Returns:
        Python function definition as string
        
    Example output:
        ```python
        def compute_total_revenue(record: Company, context: ComputationContext) -> float:
            \"\"\"
            Rollup Total Revenue from deals using SUM
            \"\"\"
            return context.rollup("deals", "revenue", "SUM")
        ```
    """
    field_metadata = field_info.metadata
    if not field_metadata:
        return _generate_stub_function(field_info, "Rollup metadata missing")
    
    options_dict = field_metadata.get("options", {})
    link_field_id = options_dict.get("recordLinkFieldId")
    target_field_id = options_dict.get("fieldIdInLinkedTable")
    aggregation = options_dict.get("aggregationFunction", "SUM")
    
    if not link_field_id or not target_field_id:
        return _generate_stub_function(field_info, "Rollup configuration incomplete")
    
    # Find link field and target field names
    link_field = _find_field_info_by_id(metadata, link_field_id)
    target_field = _find_field_info_by_id(metadata, target_field_id)
    
    if not link_field or not target_field:
        return _generate_stub_function(field_info, "Linked fields not found")
    
    link_field_name = _to_snake_case(link_field["name"])
    target_field_name = _to_snake_case(target_field["name"])
    
    # Generate function
    func_name = field_info.function_name or f"compute_{_to_snake_case(field_info.name)}"
    
    # Generate null checks if enabled
    null_check_code = ""
    if options.include_null_checks:
        if options.data_access_mode == "dict":
            check_expr = f'record.get("{link_field_name}") is None'
        else:
            check_expr = f'record.{link_field_name} is None'
        
        null_check_code = f"""    # Null safety check
    if {check_expr}:
        return None
    
"""
    
    parts = []
    
    # Function signature
    if options.include_type_hints:
        parts.append(f"def {func_name}(record, context: 'ComputationContext') -> Any:")
    else:
        parts.append(f"def {func_name}(record, context):")
    
    # Docstring
    if options.include_docstrings:
        parts.append(f'''    """
    Rollup {field_info.name} from {link_field["name"]} using {aggregation}
    """''')
    
    # Null check
    if null_check_code:
        parts.append(null_check_code)
    
    # Rollup code
    parts.append(f'    return context.rollup("{link_field_name}", "{target_field_name}", "{aggregation}")')
    
    return "\n".join(parts)


def _generate_stub_function(field_info: FieldInfo, reason: str) -> str:
    """Generate a stub function that returns None with a comment explaining why."""
    func_name = field_info.function_name or f"compute_{_to_snake_case(field_info.name)}"
    return f"""def {func_name}(record, context):
    \"\"\"Stub for {field_info.name}: {reason}\"\"\"
    return None"""


def _find_field_info_by_id(metadata: AirtableMetadata, field_id: str) -> Optional[Dict[str, Any]]:
    """Find field metadata by ID in the schema."""
    for table in metadata["tables"]:
        for field in table["fields"]:
            if field["id"] == field_id:
                return field
    return None


# ============================================================================
# Phase 3: Update Function Generator
# ============================================================================

def generate_update_function(
    graph: ComputationGraph,
    options: GeneratorOptions
) -> str:
    """
    Generate the main update_record() function.
    
    This function orchestrates incremental computation:
    1. Accepts list of changed fields (or assumes all if empty)
    2. Processes depths in order
    3. Only recomputes fields whose dependencies changed
    4. Tracks computed fields to avoid duplicates
    
    Args:
        graph: Computation graph
        options: Generator options
    
    Returns:
        Python code string for update_record() function
    """
    parts = []
    
    # Function signature
    if options.include_type_hints:
        parts.append("def update_record(")
        parts.append("    record: Any,")
        parts.append("    context: ComputationContext,")
        parts.append("    changed_fields: Optional[List[str]] = None")
        parts.append(") -> Any:")
    else:
        parts.append("def update_record(record, context, changed_fields=None):")
    
    # Docstring
    if options.include_docstrings:
        parts.append('    """')
        parts.append("    Update a record by recomputing affected formula fields.")
        parts.append("    ")
        parts.append("    Args:")
        parts.append("        record: The record to update")
        parts.append("        context: Computation context with related records")
        parts.append("        changed_fields: List of field names that changed.")
        parts.append("                       If None or empty, assume all fields changed.")
        parts.append("    ")
        parts.append("    Returns:")
        parts.append("        Updated record with recomputed formulas")
        parts.append('    """')
    
    # Function body
    parts.append("    # Reset computation tracking")
    parts.append("    context.computed_this_cycle = set()")
    parts.append("    ")
    parts.append("    # If no changed fields specified, assume everything changed")
    parts.append("    if not changed_fields:")
    parts.append("        # Get table ID from record")
    parts.append("        if hasattr(record, '_table_id'):")
    parts.append("            table_id = record._table_id")
    parts.append("        elif hasattr(record, '__table_id__'):")
    parts.append("            table_id = record.__table_id__")
    parts.append("        else:")
    parts.append("            # Assume all fields if we can't determine table")
    parts.append("            changed_fields = list(COMPUTATION_GRAPH['field_name_to_id'].keys())")
    parts.append("        ")
    parts.append("        if 'table_id' not in locals():")
    parts.append("            pass  # Already set changed_fields")
    parts.append("        elif table_id in COMPUTATION_GRAPH['table_fields']:")
    parts.append("            changed_fields = COMPUTATION_GRAPH['table_fields'][table_id]")
    parts.append("        else:")
    parts.append("            changed_fields = list(COMPUTATION_GRAPH['field_name_to_id'].keys())")
    parts.append("    ")
    parts.append("    # Convert field names to IDs")
    parts.append("    changed_field_ids = set()")
    parts.append("    for name in changed_fields:")
    parts.append("        field_id = COMPUTATION_GRAPH['field_name_to_id'].get(name)")
    parts.append("        if field_id:")
    parts.append("            changed_field_ids.add(field_id)")
    parts.append("    ")
    parts.append("    # Track what needs recalculation")
    parts.append("    fields_to_compute = set()")
    parts.append("    ")
    
    if options.track_computation_stats:
        parts.append("    # Track computation statistics")
        parts.append("    computation_stats = {'computed': 0, 'skipped': 0}")
        parts.append("    ")
    
    parts.append("    # Process each depth level in order")
    parts.append(f"    for depth in range(COMPUTATION_GRAPH['max_depth'] + 1):")
    parts.append("        depth_fields = COMPUTATION_GRAPH['depths'].get(depth, {})")
    parts.append("        ")
    
    if options.optimize_depth_skipping:
        parts.append("        # Optimization: Skip entire depth if nothing changed")
        parts.append("        if depth > 0 and not fields_to_compute and not changed_field_ids:")
        parts.append("            continue")
        parts.append("        ")
    
    parts.append("        # Process each field at this depth")
    parts.append("        for field_id, field_info in depth_fields.items():")
    parts.append("            # Skip if not a computed field")
    parts.append("            if field_info['type'] not in COMPUTED_FIELD_TYPES:")
    parts.append("                continue")
    parts.append("            ")
    parts.append("            # Check if this field needs recomputation")
    parts.append("            should_compute = False")
    parts.append("            ")
    parts.append("            # Reason 1: Field is in the initial changed list")
    parts.append("            if field_id in changed_field_ids:")
    parts.append("                should_compute = True")
    parts.append("            ")
    parts.append("            # Reason 2: One of its dependencies changed")
    parts.append("            elif any(dep_id in fields_to_compute for dep_id in field_info['dependencies']):")
    parts.append("                should_compute = True")
    parts.append("            ")
    parts.append("            # Compute if needed")
    parts.append("            if should_compute and field_id not in context.computed_this_cycle:")
    parts.append("                field_name = field_info['name']")
    parts.append("                compute_func = FIELD_COMPUTERS.get(field_name)")
    parts.append("                ")
    parts.append("                if compute_func:")
    parts.append("                    # Compute the new value")
    parts.append("                    new_value = compute_func(record, context)")
    parts.append("                    ")
    parts.append("                    # Update the record (depends on data access mode)")
    parts.append("                    if hasattr(record, field_name):")
    parts.append("                        setattr(record, field_name, new_value)")
    parts.append("                    else:")
    parts.append("                        record[field_name] = new_value")
    parts.append("                    ")
    parts.append("                    # Mark as computed and as changed (for downstream dependencies)")
    parts.append("                    context.computed_this_cycle.add(field_id)")
    parts.append("                    fields_to_compute.add(field_id)")
    
    if options.track_computation_stats:
        parts.append("                    computation_stats['computed'] += 1")
        parts.append("            else:")
        parts.append("                computation_stats['skipped'] += 1")
    
    parts.append("    ")
    
    if options.track_computation_stats:
        parts.append("    # Store stats in context if tracking enabled")
        parts.append("    context.last_computation_stats = computation_stats")
        parts.append("    ")
    
    parts.append("    return record")
    
    return "\n".join(parts)


def generate_complete_module(
    metadata: AirtableMetadata,
    table_id: Optional[str] = None,
    options: Optional[GeneratorOptions] = None
) -> str:
    """
    Generate a complete Python module with incremental formula evaluation.
    
    The generated module includes:
    - Type definitions (dataclass/TypedDict/etc.)
    - Formula computation functions
    - ComputationContext class
    - update_record() function
    - Embedded computation graph data
    
    Args:
        metadata: Airtable metadata
        table_id: Optional - generate for single table only
        options: Generator options (uses defaults if None)
    
    Returns:
        Complete Python module as a string
    """
    if options is None:
        options = GeneratorOptions()
    
    # Phase 1: Build computation graph
    graph = build_computation_graph(metadata, table_id)
    
    # Phase 2: Generate formula functions
    formula_functions = []
    for field_info in graph.get_computed_fields():
        if field_info.field_type == FIELD_TYPE_FORMULA:
            func_code = generate_formula_function(field_info, metadata, options)
            formula_functions.append(func_code)
        elif field_info.field_type == FIELD_TYPE_LOOKUP:
            func_code = generate_lookup_function(field_info, metadata, options)
            formula_functions.append(func_code)
        elif field_info.field_type == FIELD_TYPE_ROLLUP:
            func_code = generate_rollup_function(field_info, metadata, options)
            formula_functions.append(func_code)
    
    # Phase 3: Generate context and update function
    context_class = generate_computation_context_class(graph, options)
    linked_table_map = generate_linked_table_map(graph, metadata)
    computation_graph_data = generate_computation_graph_data(graph, options)
    field_computers = generate_field_computers_mapping(graph, metadata, options)
    update_function = generate_update_function(graph, options)
    
    # Phase 4: Generate type definitions
    type_definitions = _generate_type_definitions(metadata, table_id, options)
    
    # Combine all parts
    parts = [
        _generate_module_header(options),
        type_definitions,
        "\n\n# ============================================================================",
        "# Formula Computation Functions",
        "# ============================================================================\n",
        "\n\n".join(formula_functions) if formula_functions else "# No computed fields",
        "\n\n# ============================================================================",
        "# Computation Context",
        "# ============================================================================\n",
        linked_table_map,
        "\n",
        context_class,
        "\n\n# ============================================================================",
        "# Computation Graph Data",
        "# ============================================================================\n",
        computation_graph_data,
        "\n",
        field_computers,
        "\n\n# ============================================================================",
        "# Update Function",
        "# ============================================================================\n",
        update_function,
    ]
    
    if options.include_examples:
        # parts.append(_generate_usage_examples(graph))  # Phase 5
        pass
    
    return "\n".join(parts)


def _generate_module_header(options: GeneratorOptions) -> str:
    """Generate module docstring and imports"""
    header = '''"""
Generated Formula Evaluator with Incremental Computation

This module was auto-generated from Airtable schema metadata.
It provides efficient formula evaluation by only recomputing fields
whose dependencies have actually changed.

Usage:
    from this_module import YourTable, update_record, ComputationContext
    
    # Create a record
    record = YourTable(id="rec123", field1="value1")
    
    # Create context
    context = ComputationContext(record, all_related_records)
    
    # Initial computation (all fields)
    record = update_record(record, context)
    
    # Update specific fields
    record.field1 = "new_value"
    record = update_record(record, context, changed_fields=["field1"])
"""
'''
    
    # Add imports based on data access mode
    if options.data_access_mode == "dataclass":
        header += "\nfrom dataclasses import dataclass"
    elif options.data_access_mode == "pydantic":
        header += "\nfrom pydantic import BaseModel"
    
    # Always include these
    header += "\nfrom typing import Dict, List, Optional, Any, Set, Union, Literal"
    header += "\ntry:"
    header += "\n    from typing import TypedDict, NotRequired"
    header += "\nexcept ImportError:"
    header += "\n    from typing_extensions import TypedDict, NotRequired"
    header += "\nfrom datetime import datetime"
    
    return header


def _generate_type_definitions(
    metadata: AirtableMetadata,
    table_id: Optional[str],
    options: GeneratorOptions
) -> str:
    """
    Generate type definitions for tables.
    
    Uses the types_generator module to create dataclass or TypedDict definitions.
    
    Args:
        metadata: Airtable metadata
        table_id: Optional table ID to generate for (None = all tables)
        options: Generator options
    
    Returns:
        Python code string with type definitions
    """
    sys.path.append("web")
    from types_generator import generate_python_types
    
    # Filter metadata to single table if specified
    if table_id:
        tables = [t for t in metadata.get("tables", []) if t.get("id") == table_id]
        filtered_metadata = {"tables": tables}
    else:
        filtered_metadata = metadata
    
    # Generate types based on data access mode
    use_dataclasses = options.data_access_mode in ["dataclass", "pydantic"]
    
    type_code = generate_python_types(
        filtered_metadata,
        include_helpers=False,  # Don't need attachment/collaborator helpers
        use_dataclasses=use_dataclasses,
        mark_computed_fields=True  # Mark computed fields with comments
    )
    
    # Remove the module docstring from types_generator (we have our own)
    lines = type_code.split("\n")
    # Skip first 3 lines (docstring and blank lines)
    if lines and lines[0].startswith('"""'):
        # Find the closing """
        for i, line in enumerate(lines):
            if i > 0 and '"""' in line:
                lines = lines[i+1:]
                break
    
    # Also remove duplicate imports (we have them in header)
    filtered_lines = []
    for line in lines:
        if line.strip().startswith(("from dataclasses", "from typing")):
            continue  # Skip - already in header
        filtered_lines.append(line)
    
    return "\n".join(filtered_lines)


def generate_field_computers_mapping(
    graph: ComputationGraph,
    metadata: AirtableMetadata,
    options: GeneratorOptions
) -> str:
    """
    Generate the FIELD_COMPUTERS mapping of field names to computation functions.
    
    Args:
        graph: Computation graph
        metadata: Airtable metadata
        options: Generator options
    
    Returns:
        Python code string for FIELD_COMPUTERS dict
    """
    parts = []
    parts.append("# Mapping of field names to computation functions")
    parts.append("FIELD_COMPUTERS = {")
    
    computed_fields = graph.get_computed_fields()
    for field_info in computed_fields:
        if field_info.function_name:
            field_name_snake = _to_snake_case(field_info.name)
            parts.append(f'    "{field_name_snake}": {field_info.function_name},')
    
    parts.append("}")
    
    return "\n".join(parts)


def generate_computation_graph_data(
    graph: ComputationGraph,
    options: GeneratorOptions
) -> str:
    """
    Generate the COMPUTATION_GRAPH data structure as Python code.
    
    This embeds the computation graph into the generated module so the
    update function can use it at runtime.
    
    Args:
        graph: Computation graph
        options: Generator options
    
    Returns:
        Python code string for COMPUTATION_GRAPH dict
    """
    import json
    
    parts = []
    parts.append("# Computation graph data structure")
    parts.append("COMPUTATION_GRAPH = {")
    parts.append(f"    'max_depth': {graph.max_depth},")
    parts.append("    'depths': {")
    
    # Generate depths dictionary
    for depth in sorted(graph.depths.keys()):
        parts.append(f"        {depth}: {{")
        depth_fields = graph.depths[depth]
        
        for field_id, field_info in depth_fields.items():
            parts.append(f"            '{field_id}': {{")
            parts.append(f"                'name': '{_to_snake_case(field_info.name)}',")
            parts.append(f"                'type': '{field_info.field_type}',")
            parts.append(f"                'table_id': '{field_info.table_id}',")
            parts.append(f"                'dependencies': {json.dumps(field_info.dependencies)},")
            parts.append(f"                'dependents': {json.dumps(field_info.dependents)},")
            if field_info.function_name:
                parts.append(f"                'function_name': '{field_info.function_name}',")
            parts.append("            },")
        
        parts.append("        },")
    
    parts.append("    },")
    
    # Field ID to name mapping
    parts.append("    'field_id_to_name': {")
    for field_id, name in graph.field_id_to_name.items():
        parts.append(f"        '{field_id}': '{_to_snake_case(name)}',")
    parts.append("    },")
    
    # Field name to ID mapping
    parts.append("    'field_name_to_id': {")
    for name, field_id in graph.field_name_to_id.items():
        parts.append(f"        '{_to_snake_case(name)}': '{field_id}',")
    parts.append("    },")
    
    # Table fields mapping
    parts.append("    'table_fields': {")
    for table_id, field_names in graph.table_fields.items():
        snake_names = [_to_snake_case(name) for name in field_names]
        parts.append(f"        '{table_id}': {json.dumps(snake_names)},")
    parts.append("    },")
    
    parts.append("}")
    parts.append("")
    parts.append("# Computed field types for filtering")
    parts.append(f"COMPUTED_FIELD_TYPES = {json.dumps(list(COMPUTED_FIELD_TYPES))}")
    
    return "\n".join(parts)


def generate_linked_table_map(
    graph: ComputationGraph,
    metadata: AirtableMetadata
) -> str:
    """
    Generate LINKED_TABLE_MAP for lookup/rollup operations.
    
    Maps link field names to their target table IDs.
    
    Args:
        graph: Computation graph
        metadata: Airtable metadata
    
    Returns:
        Python code string for LINKED_TABLE_MAP dict
    """
    parts = []
    parts.append("# Mapping of link field names to target table IDs")
    parts.append("LINKED_TABLE_MAP = {")
    
    # Find all multipleRecordLinks fields
    for table in metadata["tables"]:
        for field in table["fields"]:
            if field["type"] == "multipleRecordLinks":
                field_name_snake = _to_snake_case(field["name"])
                linked_table_id = field.get("options", {}).get("linkedTableId", "")
                if linked_table_id:
                    parts.append(f'    "{field_name_snake}": "{linked_table_id}",')
    
    parts.append("}")
    
    return "\n".join(parts)


def _to_snake_case(name: str) -> str:
    """Convert a name to snake_case for use as Python identifier"""
    # Replace spaces and special chars with underscores
    import re
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # Convert camelCase to snake_case
    name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    # Convert to lowercase
    name = name.lower()
    # Remove duplicate underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    'GeneratorOptions',
    'ComputationGraph',
    'FieldInfo',
    'build_computation_graph',
    'generate_formula_function',
    'generate_lookup_function',
    'generate_rollup_function',
    'generate_computation_context_class',
    'generate_update_function',
    'generate_field_computers_mapping',
    'generate_computation_graph_data',
    'generate_linked_table_map',
    'generate_complete_module',
]
