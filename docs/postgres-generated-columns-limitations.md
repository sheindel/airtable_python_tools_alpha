# PostgreSQL Generated Columns and Immutability Constraints

## The Problem

When generating PostgreSQL schemas from Airtable metadata with formulas converted to `GENERATED ALWAYS AS` columns, you may encounter this error:

```
ERROR: 42P17: generation expression is not immutable
```

## Understanding the Error

PostgreSQL's `GENERATED ALWAYS AS` columns have a strict requirement: **the expression must be immutable**. This means:

1. The expression must always return the same result for the same input values
2. It cannot depend on:
   - Current time (unless using immutable date functions)
   - Database state
   - Random values
   - **Array comparison or manipulation functions** (many are not immutable)

### Why Array Operations Cause Problems

The error in your case was caused by formulas that reference **array-typed fields** (`TEXT[]`). For example:

```sql
-- PROBLEMATIC: Comparing array to empty string
companies_combined TEXT GENERATED ALWAYS AS (
  CASE WHEN company='' THEN ...  -- company is TEXT[], can't compare to ''
```

Common array issues:
- **`array = ''`** - Invalid comparison between array and text
- **`array_length(array, 1)`** - NOT immutable in PostgreSQL
- **`array_to_string(arrays)`** - NOT immutable for generated columns
- **`COALESCE(array, ARRAY[])`** - NOT immutable

## The Solution Implemented

The code now **validates formulas before attempting conversion** and skips formulas that reference array fields:

### What Changed

1. **Enhanced `is_formula_convertible()` function** ([airtable_formula_to_sql.py](../web/airtable_formula_to_sql.py)):
   ```python
   def is_formula_convertible(
       formula: str,
       field_name_map: Optional[Dict[str, str]] = None,
       field_type_map: Optional[Dict[str, str]] = None
   ) -> bool:
       # ... existing checks ...
       
       # NEW: Check if formula references array fields
       if field_name_map and field_type_map:
           field_refs = re.findall(r'\{([^}]+)\}', formula)
           for field_ref in field_refs:
               column_name = field_name_map.get(field_ref)
               if column_name and column_name in field_type_map:
                   col_type = field_type_map[column_name]
                   # Array types cannot be used in generated columns
                   if col_type and col_type.endswith('[]'):
                       return False
       return True
   ```

2. **Updated schema generator** ([postgres_schema_generator.py](../web/tabs/postgres_schema.py)):
   - Builds a `field_type_map` before processing formulas
   - Passes type information to `is_formula_convertible()`
   - Formulas referencing arrays are skipped with a comment

### Example Output

Before (causes error):
```sql
CREATE TABLE contacts (
    company TEXT[],
    dm_for TEXT[],
    companies_combined TEXT GENERATED ALWAYS AS (
        CASE WHEN company='' THEN dm_for ELSE company END  -- ERROR!
    ) STORED
);
```

After (safe):
```sql
CREATE TABLE contacts (
    company TEXT[],
    dm_for TEXT[],
    -- companies_combined: Formula not convertible (array dependencies)
);
```

## Alternative Approaches

If you need computed columns based on array fields, consider these alternatives:

### Option 1: Regular Column + Triggers (Recommended)

Instead of `GENERATED ALWAYS AS`, use a regular column updated by triggers:

```sql
CREATE TABLE contacts (
    company TEXT[],
    dm_for TEXT[],
    companies_combined TEXT  -- Regular column, not generated
);

CREATE OR REPLACE FUNCTION update_companies_combined()
RETURNS TRIGGER AS $$
BEGIN
    NEW.companies_combined := CASE
        WHEN cardinality(NEW.company) > 0 THEN NEW.company[1]
        WHEN cardinality(NEW.dm_for) > 0 THEN NEW.dm_for[1]
        ELSE NULL
    END;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_companies_combined
    BEFORE INSERT OR UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_companies_combined();
```

**Pros:**
- Can use non-immutable functions
- More flexible logic
- Still automatically updated

**Cons:**
- More complex setup
- Trigger overhead on writes

### Option 2: Materialize Only Non-Array Formulas

The current implementation automatically does this:
- Formulas using only scalar fields → `GENERATED ALWAYS AS`
- Formulas using any array fields → Skipped (add as comment)

**Example of safe formulas:**
```sql
-- ✅ SAFE: Only scalar fields
name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED

-- ✅ SAFE: Date logic with scalar fields
source_date DATE GENERATED ALWAYS AS (
    CASE WHEN ovrd_source_time IS NULL 
         THEN create_date 
         ELSE ovrd_source_time 
    END
) STORED
```

### Option 3: Application-Level Computation

Compute values in your application code rather than in the database:
```python
def get_companies_combined(record):
    if record['company']:
        return record['company']
    elif record['dm_for']:
        return record['dm_for']
    else:
        return record['billing_for']
```

**Pros:**
- Maximum flexibility
- No database limitations

**Cons:**
- Value not stored in database
- Needs recomputation on every read
- Can't filter/sort by this field in SQL

## When to Use Each Approach

| Scenario | Recommended Approach |
|----------|---------------------|
| Simple scalar field formulas | `GENERATED ALWAYS AS` (automatic) |
| Formulas with array fields | Triggers or application logic |
| Complex business logic | Application-level computation |
| Need to filter/sort by computed value | Triggers (indexed regular column) |
| Read-heavy workload | `GENERATED ALWAYS AS` or triggers |
| Write-heavy workload | Application logic (no trigger overhead) |

## Testing

Tests validate the array field detection:

```python
def test_array_field_reference_not_convertible():
    """Formulas referencing array fields are not convertible"""
    formula = "IF({fld123} = '', 'Empty', 'Not Empty')"
    field_map = {"fld123": "company"}
    field_type_map = {"company": "TEXT[]"}
    
    # Should be rejected
    assert is_formula_convertible(formula, field_map, field_type_map) is False

def test_non_array_field_reference_is_convertible():
    """Formulas with non-array fields are still convertible"""
    formula = "IF({fld123} = '', 'Empty', 'Not Empty')"
    field_map = {"fld123": "name"}
    field_type_map = {"name": "TEXT"}
    
    # Should be accepted
    assert is_formula_convertible(formula, field_map, field_type_map) is True
```

## Summary

**The fix:** Formulas that reference array-typed fields are now automatically detected and skipped during PostgreSQL schema generation, preventing the "generation expression is not immutable" error.

**Your options:**
1. **Accept skipped formulas** - Safest, zero risk
2. **Use triggers** - Flexible, supports array operations
3. **Compute in application** - Maximum control, no DB limitations

For most use cases, the automatic filtering (option 1) is sufficient. For critical computed fields involving arrays, implement triggers (option 2).
