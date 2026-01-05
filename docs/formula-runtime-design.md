# Formula Runtime Generator - Design Document

**Status**: Phase 4 Planning  
**Created**: January 2, 2026  
**Related Tools**: Types Generator, Formula Compressor, Dependency Mapper

## Overview

This document outlines the design for a **Formula Runtime Generator** system that converts Airtable computed fields (formulas, lookups, rollups) into executable code across multiple platforms. The core innovation is an **abstract tokenized formula representation** that enables transpilation to Python, JavaScript, SQL, and other target languages.

## Goals

1. **Generate executable getter functions** for computed fields that can run in any environment
2. **Abstract formula representation** that decouples Airtable syntax from target platform
3. **Dependency-ordered execution** to ensure correct calculation sequencing
4. **Multiple deployment targets**: Python SDK, JavaScript library, SQL triggers, API servers
5. **Integration with existing Types Generator** (rename to Code/Library Generator)

## Non-Goals (for initial implementation)

- Real-time formula editing/compilation
- Support for all Airtable formula functions immediately (incremental support)
- Circular dependency resolution (assumes Airtable prevents these)
- Formula optimization/algebraic simplification

---

## Architecture

### Phase 1: Abstract Formula Layer

#### 1.1 Formula Tokenizer/Parser

**Location**: `web/at_formula_parser.py` (expand existing module)

Convert Airtable formula strings into an Abstract Syntax Tree (AST):

```python
@dataclass
class FormulaNode:
    """Base class for all formula AST nodes"""
    node_type: str
    
@dataclass
class LiteralNode(FormulaNode):
    """Represents a literal value: 42, "hello", true"""
    value: Any
    data_type: str  # "number", "string", "boolean"
    
@dataclass
class FieldReferenceNode(FormulaNode):
    """Reference to another field: {fldXXXXXXXXXXXXXX}"""
    field_id: str
    field_name: str
    field_type: str
    
@dataclass
class FunctionCallNode(FormulaNode):
    """Function invocation: IF(condition, true_val, false_val)"""
    function_name: str
    arguments: List[FormulaNode]
    
@dataclass
class BinaryOpNode(FormulaNode):
    """Binary operations: +, -, *, /, &, =, !=, <, >, etc."""
    operator: str
    left: FormulaNode
    right: FormulaNode
    
@dataclass
class UnaryOpNode(FormulaNode):
    """Unary operations: -, NOT"""
    operator: str
    operand: FormulaNode
```

**Key Function**:
```python
def parse_airtable_formula(formula: str, metadata: dict) -> FormulaNode:
    """
    Parse Airtable formula string into AST.
    
    Handles:
    - Field references: {fldXXXXXXXXXXXXXX}
    - String literals: "hello"
    - Number literals: 42, 3.14
    - Boolean literals: true, false
    - Function calls: IF(...), CONCATENATE(...), SUM(...)
    - Operators: +, -, *, /, &, =, !=, <, >, <=, >=
    - Parentheses for grouping
    """
    pass
```

#### 1.2 Formula Depth Calculator

**Location**: `web/at_metadata_graph.py` (extend existing)

```python
def get_formula_depth(field_id: str, G: nx.DiGraph) -> int:
    """
    Calculate the dependency depth of a formula field.
    
    Depth 0: Basic fields (no dependencies)
    Depth 1: Formulas that only reference basic fields
    Depth 2: Formulas that reference depth-1 formulas
    Etc.
    
    Uses backward traversal of dependency graph.
    """
    pass

def get_computation_order(metadata: dict) -> List[List[str]]:
    """
    Return field IDs grouped by computation depth.
    
    Returns:
        [[depth_0_fields], [depth_1_fields], [depth_2_fields], ...]
    
    Fields within the same depth can be computed in parallel.
    Fields must be computed in depth order.
    """
    pass
```

---

### Phase 2: Python Code Generator (MVP)

#### 2.1 Python Transpiler

**Location**: `web/code_generators/python_runtime_generator.py` (new)

```python
class PythonFormulaTranspiler:
    """Convert FormulaNode AST to Python code"""
    
    def __init__(self, data_access_mode: str = "dataclass"):
        """
        Args:
            data_access_mode: How to access record fields
                - "dataclass": record.field_name
                - "dict": record["field_name"]
                - "orm": record.field_name (SQLAlchemy-style)
        """
        self.data_access_mode = data_access_mode
    
    def transpile(self, node: FormulaNode) -> str:
        """Convert AST node to Python expression"""
        if isinstance(node, LiteralNode):
            return self._transpile_literal(node)
        elif isinstance(node, FieldReferenceNode):
            return self._transpile_field_reference(node)
        elif isinstance(node, FunctionCallNode):
            return self._transpile_function_call(node)
        elif isinstance(node, BinaryOpNode):
            return self._transpile_binary_op(node)
        elif isinstance(node, UnaryOpNode):
            return self._transpile_unary_op(node)
    
    def _transpile_field_reference(self, node: FieldReferenceNode) -> str:
        """
        Convert field reference to data access pattern.
        
        Example outputs:
        - dataclass: "record.customer_name"
        - dict: "record['customer_name']"
        - orm: "record.customer_name"
        """
        pass
    
    def _transpile_function_call(self, node: FunctionCallNode) -> str:
        """
        Map Airtable functions to Python equivalents.
        
        Examples:
        - IF(cond, true, false) → (true_val if cond else false_val)
        - CONCATENATE(a, b) → str(a) + str(b)
        - LEN(text) → len(str(text))
        - ROUND(num, precision) → round(num, precision)
        """
        pass
```

#### 2.2 Lookup/Rollup Generator

```python
class PythonLookupTranspiler:
    """Generate code for lookup and rollup fields"""
    
    def generate_lookup_getter(
        self, 
        field: dict, 
        metadata: dict,
        data_access_mode: str
    ) -> str:
        """
        Generate getter for lookup field.
        
        Requires:
        - Link field to traverse
        - Field to lookup in related record
        - Data access interface for related records
        
        Example output:
        def get_customer_email(self, record) -> Optional[str]:
            linked_record_id = record.customer_id
            if not linked_record_id:
                return None
            customer = self.data_access.get_customer(linked_record_id)
            return customer.email if customer else None
        """
        pass
    
    def generate_rollup_getter(
        self,
        field: dict,
        metadata: dict,
        data_access_mode: str
    ) -> str:
        """
        Generate getter for rollup field.
        
        Requires:
        - Link field to traverse (may link to multiple records)
        - Field to rollup in related records
        - Aggregation function (SUM, COUNT, MAX, etc.)
        - Data access interface for related records
        
        Example output:
        def get_total_order_value(self, record) -> float:
            order_ids = record.orders or []
            if not order_ids:
                return 0.0
            orders = self.data_access.get_orders_batch(order_ids)
            return sum(order.value for order in orders)
        """
        pass
```

#### 2.3 Complete Python Library Generator

```python
def generate_python_library(
    metadata: dict,
    options: dict
) -> str:
    """
    Generate complete Python module with computed field getters.
    
    Args:
        metadata: Airtable metadata
        options:
            - data_access_mode: "dataclass" | "dict" | "orm"
            - include_types: bool (generate dataclass definitions)
            - execution_mode: "lazy" | "eager"
            - include_helpers: bool (include runtime helper functions)
    
    Returns:
        Complete Python module as string
    
    Generated code structure:
    ```python
    # Auto-generated from Airtable metadata
    # Generated: 2026-01-02
    
    from typing import Optional, List, Protocol
    from dataclasses import dataclass
    
    # Data access interface
    class DataAccess(Protocol):
        def get_customer(self, record_id: str) -> Optional['Customer']:
            ...
        def get_orders_batch(self, record_ids: List[str]) -> List['Order']:
            ...
    
    # Dataclass definitions (if include_types=True)
    @dataclass
    class Order:
        id: str
        customer_id: str
        amount: float
        # ... basic fields only
    
    # Computed field getters
    class OrderComputedFields:
        def __init__(self, data_access: DataAccess):
            self.data_access = data_access
        
        # Depth 1 formulas
        def get_tax_amount(self, record: Order) -> float:
            return record.amount * 0.08
        
        def get_customer_email(self, record: Order) -> Optional[str]:
            # Lookup implementation
            ...
        
        # Depth 2 formulas (depend on depth 1)
        def get_total_with_tax(self, record: Order) -> float:
            base = record.amount
            tax = self.get_tax_amount(record)
            return base + tax
    ```
    """
    pass
```

---

### Phase 3: JavaScript Code Generator

**Location**: `web/code_generators/javascript_runtime_generator.py`

Similar architecture to Python generator, but outputs:
- ES6 classes
- TypeScript type definitions (optional)
- Async/await for data access
- Browser-compatible or Node.js-compatible

```javascript
// Example output
class OrderComputedFields {
  constructor(dataAccess) {
    this.dataAccess = dataAccess;
  }
  
  // Depth 1
  getTaxAmount(record) {
    return record.amount * 0.08;
  }
  
  async getCustomerEmail(record) {
    if (!record.customerId) return null;
    const customer = await this.dataAccess.getCustomer(record.customerId);
    return customer?.email ?? null;
  }
  
  // Depth 2
  getTotalWithTax(record) {
    const base = record.amount;
    const tax = this.getTaxAmount(record);
    return base + tax;
  }
}
```

---

### Phase 4: SQL Generator

**Location**: `web/code_generators/sql_runtime_generator.py`

Most complex due to SQL's declarative nature. Two approaches:

#### 4.1 SQL Functions/Views (Read-time calculation)

```sql
-- Example output: Computed columns as SQL functions

-- Depth 1 formula
CREATE FUNCTION get_tax_amount(order_id UUID)
RETURNS DECIMAL AS $$
  SELECT amount * 0.08
  FROM orders
  WHERE id = order_id;
$$ LANGUAGE SQL IMMUTABLE;

-- Depth 1 lookup
CREATE FUNCTION get_customer_email(order_id UUID)
RETURNS TEXT AS $$
  SELECT c.email
  FROM orders o
  JOIN customers c ON o.customer_id = c.id
  WHERE o.id = order_id;
$$ LANGUAGE SQL STABLE;

-- Depth 2 formula
CREATE FUNCTION get_total_with_tax(order_id UUID)
RETURNS DECIMAL AS $$
  SELECT amount + get_tax_amount(order_id)
  FROM orders
  WHERE id = order_id;
$$ LANGUAGE SQL IMMUTABLE;

-- View combining all computed fields
CREATE VIEW orders_with_computed AS
SELECT 
  o.*,
  get_tax_amount(o.id) AS tax_amount,
  get_customer_email(o.id) AS customer_email,
  get_total_with_tax(o.id) AS total_with_tax
FROM orders o;
```

#### 4.2 SQL Triggers (Write-time calculation)

```sql
-- Example output: Triggers to populate computed columns on INSERT/UPDATE

CREATE OR REPLACE FUNCTION update_order_computed_fields()
RETURNS TRIGGER AS $$
BEGIN
  -- Depth 1 calculations
  NEW.tax_amount := NEW.amount * 0.08;
  
  NEW.customer_email := (
    SELECT email 
    FROM customers 
    WHERE id = NEW.customer_id
  );
  
  -- Depth 2 calculations (depend on depth 1)
  NEW.total_with_tax := NEW.amount + NEW.tax_amount;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_computed_fields_trigger
  BEFORE INSERT OR UPDATE ON orders
  FOR EACH ROW
  EXECUTE FUNCTION update_order_computed_fields();
```

---

### Phase 5: Web UI Integration

#### 5.1 Extend Types Generator Tab

**Location**: `web/tabs/types_generator.py` → rename to `code_generator.py`

Add new options to the UI:

```html
<!-- New section in the tab -->
<div class="option-group">
  <h3>Runtime Code Generation</h3>
  
  <label>
    <input type="checkbox" id="include-formulas">
    Generate computed field getters
  </label>
  
  <label>
    Target Platform:
    <select id="runtime-platform">
      <option value="python">Python</option>
      <option value="javascript">JavaScript</option>
      <option value="typescript">TypeScript</option>
      <option value="sql-functions">SQL Functions</option>
      <option value="sql-triggers">SQL Triggers</option>
    </select>
  </label>
  
  <label>
    Data Access Mode:
    <select id="data-access-mode">
      <option value="dataclass">Python Dataclass</option>
      <option value="dict">Python Dict</option>
      <option value="orm">ORM (SQLAlchemy/Prisma)</option>
      <option value="interface">Custom Interface</option>
    </select>
  </label>
  
  <label>
    <input type="checkbox" id="include-dependency-order">
    Include computation order comments
  </label>
  
  <label>
    <input type="checkbox" id="optimize-formulas">
    Optimize formula code (inline simple expressions)
  </label>
</div>
```

#### 5.2 New "Runtime Preview" Tab

**Location**: `web/tabs/runtime_preview.py` (new)

Interactive tool to:
1. Select a table
2. Choose platform and options
3. Preview generated code
4. Test execution with sample data
5. Download generated library

---

## Implementation Phases

### Phase 4.1: Foundation (Week 1)
- [x] Design document (this file)
- [ ] Expand `at_formula_parser.py` with full AST support
- [ ] Add `get_formula_depth()` and `get_computation_order()` to graph module
- [ ] Write comprehensive tests for parser and depth calculator

### Phase 4.2: Python MVP (Week 2-3)
- [ ] Implement `PythonFormulaTranspiler` for basic formulas
- [ ] Add support for 20+ common Airtable functions
- [ ] Implement lookup/rollup generators
- [ ] Create `generate_python_library()` function
- [ ] Add tests with real Airtable metadata examples

### Phase 4.3: UI Integration (Week 3-4)
- [ ] Rename Types Generator to Code Generator
- [ ] Add formula runtime options to UI
- [ ] Wire up Python generator to web interface
- [ ] Add download functionality for generated code

### Phase 4.4: JavaScript Generator (Week 5)
- [ ] Implement `JavaScriptFormulaTranspiler`
- [ ] Port function mappings to JS equivalents
- [ ] Generate async/await for lookups/rollups
- [ ] Add TypeScript type definition generation

### Phase 4.5: SQL Generator (Week 6-7)
- [ ] Implement SQL function generator
- [ ] Implement SQL trigger generator
- [ ] Handle SQL-specific challenges (NULL handling, joins)
- [ ] Generate migration scripts

### Phase 4.6: Advanced Features (Week 8+)
- [ ] Formula optimization (constant folding, dead code elimination)
- [ ] Performance profiling (identify slow formulas)
- [ ] Incremental computation (cache intermediate results)
- [ ] Formula testing framework (generate unit tests)

---

## Technical Specifications

### Formula Function Coverage

Start with most common functions, expand incrementally:

**Priority 1 (MVP):**
- Math: `+`, `-`, `*`, `/`, `ROUND`, `ABS`, `MOD`
- String: `CONCATENATE`, `&`, `LEN`, `UPPER`, `LOWER`, `TRIM`, `SUBSTITUTE`
- Logic: `IF`, `AND`, `OR`, `NOT`, `=`, `!=`, `<`, `>`, `<=`, `>=`
- Date: `NOW`, `TODAY`, `YEAR`, `MONTH`, `DAY`, `DATEADD`, `DATETIME_DIFF`

**Priority 2:**
- Math: `CEILING`, `FLOOR`, `SQRT`, `POWER`, `EXP`, `LOG`
- String: `LEFT`, `RIGHT`, `MID`, `FIND`, `REPLACE`, `REPT`
- Logic: `SWITCH`, `XOR`, `BLANK`, `ERROR`
- Date: `HOUR`, `MINUTE`, `SECOND`, `WEEKDAY`, `WORKDAY`
- Array: `ARRAYCOMPACT`, `ARRAYFLATTEN`, `ARRAYUNIQUE`

**Priority 3:**
- Specialized: `ENCODE_URL_COMPONENT`, `REGEX_MATCH`, `REGEX_REPLACE`
- Aggregation in context: `SUM`, `COUNT`, `MAX`, `MIN`, `AVERAGE`

### Data Access Interface

Generic interface pattern for all platforms:

```python
# Python
class DataAccessInterface(Protocol):
    """User must implement this for their data source"""
    
    def get_record(self, table_name: str, record_id: str) -> Optional[dict]:
        """Fetch single record by ID"""
        pass
    
    def get_records_batch(self, table_name: str, record_ids: List[str]) -> List[dict]:
        """Fetch multiple records (for efficient rollups)"""
        pass
    
    def get_related_records(self, table_name: str, link_field: str, record_id: str) -> List[dict]:
        """Fetch records linked via a specific field"""
        pass
```

### Error Handling

Generated code should handle:
- Missing field values (NULL/None handling)
- Type coercion (Airtable is lenient, generated code should be too)
- Division by zero
- Invalid date operations
- Missing related records

Example:
```python
def get_computed_field(self, record) -> Optional[float]:
    try:
        value = record.amount
        if value is None:
            return None
        return value * 1.08
    except (AttributeError, TypeError, ValueError):
        return None  # Graceful degradation
```

---

## Performance Considerations

### Lazy vs Eager Evaluation

**Lazy (default):**
- Compute values on-demand via getter methods
- Better for sparse access patterns
- Lower memory footprint

**Eager:**
- Compute all formulas once, return enriched object
- Better for full object serialization
- Single pass through dependency graph

### Caching Strategy

For expensive lookups/rollups, optionally generate caching:
```python
from functools import lru_cache

class OrderComputedFields:
    @lru_cache(maxsize=1000)
    def get_customer_data(self, customer_id: str):
        """Cache customer lookups"""
        return self.data_access.get_customer(customer_id)
```

### Batch Operations

Generate batch-aware code for rollups:
```python
def compute_all_orders(self, orders: List[Order]) -> List[dict]:
    """
    Compute all formulas for multiple records efficiently.
    
    Batches related record fetches to minimize queries.
    """
    # Collect all customer IDs
    customer_ids = {o.customer_id for o in orders if o.customer_id}
    
    # Fetch in one query
    customers = self.data_access.get_customers_batch(customer_ids)
    customer_map = {c.id: c for c in customers}
    
    # Compute formulas using cached lookups
    results = []
    for order in orders:
        results.append({
            'tax_amount': self.get_tax_amount(order),
            'customer_email': customer_map.get(order.customer_id, {}).get('email'),
            'total_with_tax': self.get_total_with_tax(order)
        })
    
    return results
```

---

## Testing Strategy

### Unit Tests

**Parser tests** (`tests/test_formula_parser.py`):
```python
def test_parse_simple_formula():
    ast = parse_airtable_formula("1 + 2", {})
    assert isinstance(ast, BinaryOpNode)
    assert ast.operator == "+"
    assert ast.left.value == 1
    assert ast.right.value == 2

def test_parse_field_reference():
    metadata = {...}  # Include field definitions
    ast = parse_airtable_formula("{fldXXXXXXXXXXXXXX} * 2", metadata)
    assert isinstance(ast, BinaryOpNode)
    assert isinstance(ast.left, FieldReferenceNode)
```

**Transpiler tests** (`tests/test_python_transpiler.py`):
```python
def test_transpile_arithmetic():
    node = BinaryOpNode("+", LiteralNode(1), LiteralNode(2))
    transpiler = PythonFormulaTranspiler()
    code = transpiler.transpile(node)
    assert code == "(1 + 2)"
    
def test_transpile_field_access():
    node = FieldReferenceNode("fldXXXX", "amount", "number")
    transpiler = PythonFormulaTranspiler(data_access_mode="dataclass")
    code = transpiler.transpile(node)
    assert code == "record.amount"
```

### Integration Tests

Use real Airtable metadata files:
```python
def test_generate_full_library_crm():
    with open("crm_schema.json") as f:
        metadata = json.load(f)
    
    code = generate_python_library(metadata, {
        "data_access_mode": "dataclass",
        "include_types": True
    })
    
    # Verify generated code is valid Python
    compile(code, "<generated>", "exec")
    
    # Verify expected functions exist
    assert "def get_total_revenue(" in code
    assert "class DataAccess(Protocol):" in code
```

### End-to-End Tests

Execute generated code with sample data:
```python
def test_execute_generated_formulas():
    # Generate code
    code = generate_python_library(metadata, options)
    
    # Load into namespace
    namespace = {}
    exec(code, namespace)
    
    # Create test data
    mock_data_access = MockDataAccess(...)
    computed = namespace['OrderComputedFields'](mock_data_access)
    
    test_order = Order(id="rec123", amount=100.0, customer_id="cus456")
    
    # Execute generated formulas
    tax = computed.get_tax_amount(test_order)
    assert tax == 8.0
    
    total = computed.get_total_with_tax(test_order)
    assert total == 108.0
```

---

## Dependencies

### New Dependencies

None required for Python MVP - use stdlib only:
- `ast` module for AST manipulation
- `re` for formula parsing
- Existing `networkx` for dependency ordering

### Optional Dependencies (future)

- `black` - Format generated Python code
- `prettier` - Format generated JavaScript code
- `sqlparse` - Format generated SQL code

---

## Documentation

### User Documentation

Create `docs/formula-runtime-usage.md`:
- How to generate runtime code
- How to implement DataAccess interface
- Deployment examples for each platform
- Performance tuning guide

### API Documentation

Document generated code structure:
- Class/function naming conventions
- Method signatures
- Error handling behavior
- Thread safety guarantees

---

## Open Questions

1. **Should we support custom formula functions?**
   - User-defined functions in Airtable scripts
   - How to transpile these?

2. **How to handle Airtable-specific types?**
   - Attachments, barcodes, buttons
   - May not have direct equivalents in all platforms

3. **Should we generate tests for the generated code?**
   - Property-based tests?
   - Sample data generation?

4. **How to handle formula versioning?**
   - If Airtable formula changes, regenerate code?
   - Migration strategy?

5. **Should we support incremental updates?**
   - Generate only changed formulas?
   - Merge with existing generated code?

---

## Success Metrics

- ✅ **Parser coverage**: Successfully parse 95%+ of real-world formulas
- ✅ **Function coverage**: Support 50+ Airtable formula functions
- ✅ **Performance**: Generated code runs within 2x of native Airtable calculation speed
- ✅ **Adoption**: Users deploy generated code to production environments
- ✅ **Correctness**: Generated formulas produce identical results to Airtable (within floating point precision)

---

## Future Enhancements

### Phase 5: Advanced Features

1. **Formula Optimization**
   - Constant folding: `2 + 3` → `5`
   - Common subexpression elimination
   - Dead code elimination

2. **Incremental Computation**
   - Track which fields changed
   - Recompute only affected downstream formulas
   - Generate dependency-aware update logic

3. **Formula Testing Framework**
   - Generate unit tests for each formula
   - Property-based testing (hypothesis/fast-check)
   - Regression testing against Airtable API

4. **Visual Formula Debugger**
   - Step through formula execution
   - Visualize intermediate values
   - Highlight field dependencies in real-time

5. **Performance Profiling**
   - Instrument generated code with timing
   - Identify slowest formulas
   - Suggest optimization opportunities

6. **Multi-language SDK**
   - Generate client SDKs in multiple languages
   - Shared core logic, platform-specific bindings
   - Consistent API across platforms

---

## Related Systems

This feature integrates with:

- **[Types Generator](web/tabs/types_generator.py)**: Generates basic type definitions, will be extended
- **[Formula Compressor](web/tabs/formula_compressor.py)**: Shares formula parsing/manipulation logic
- **[Dependency Mapper](web/tabs/dependency_mapper.py)**: Uses same graph traversal for depth calculation
- **[Complexity Scorecard](web/tabs/complexity_scorecard.py)**: Could use generated code complexity metrics
- **[at_metadata_graph.py](web/at_metadata_graph.py)**: Core dependency graph, add computation ordering

---

## Migration Path

This is a major feature addition. Recommended rollout:

1. **Alpha (Internal testing)**: Python generator, CLI only
2. **Beta (Limited release)**: Web UI, Python + JavaScript
3. **GA (General availability)**: All platforms, full documentation
4. **v2 (Optimization)**: Performance features, advanced options

Maintain backwards compatibility with Types Generator. Users without formula runtime enabled see no changes.
