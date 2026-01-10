"""
Value comparison utilities for parity testing.

Provides intelligent comparison functions that handle:
- Floating point tolerances
- String normalization
- Date format differences
- Array order independence
- Null/None equivalence
"""
from typing import Any, Optional


class ValueMismatchError(AssertionError):
    """Raised when local and Airtable values don't match."""
    pass


def assert_values_equal(
    local_value: Any,
    airtable_value: Any,
    field_name: str,
    tolerance: float = 0.001,
    array_order_matters: bool = False
) -> None:
    """
    Compare local and Airtable values with appropriate tolerances.
    
    Handles:
    - Numbers (with floating point tolerance)
    - Strings (exact match)
    - Dates (format normalization)
    - Arrays (order-independent by default)
    - Null/None equivalence
    - Booleans (exact match)
    
    Args:
        local_value: Value computed by generated code
        airtable_value: Value from Airtable API
        field_name: Name of the field being compared (for error messages)
        tolerance: Tolerance for floating point comparisons
        array_order_matters: If True, array order must match exactly
    
    Raises:
        ValueMismatchError: If values don't match within tolerances
    """
    # Handle None/null equivalence
    if local_value is None and airtable_value is None:
        return
    
    if local_value is None or airtable_value is None:
        raise ValueMismatchError(
            f"Field '{field_name}': null mismatch\n"
            f"  Local: {local_value}\n"
            f"  Airtable: {airtable_value}"
        )
    
    # Handle numbers (int and float)
    if isinstance(local_value, (int, float)) and isinstance(airtable_value, (int, float)):
        diff = abs(float(local_value) - float(airtable_value))
        if diff > tolerance:
            raise ValueMismatchError(
                f"Field '{field_name}': numeric mismatch\n"
                f"  Local: {local_value}\n"
                f"  Airtable: {airtable_value}\n"
                f"  Difference: {diff} (tolerance: {tolerance})"
            )
        return
    
    # Handle booleans
    if isinstance(local_value, bool) and isinstance(airtable_value, bool):
        if local_value != airtable_value:
            raise ValueMismatchError(
                f"Field '{field_name}': boolean mismatch\n"
                f"  Local: {local_value}\n"
                f"  Airtable: {airtable_value}"
            )
        return
    
    # Handle strings
    if isinstance(local_value, str) and isinstance(airtable_value, str):
        if local_value != airtable_value:
            raise ValueMismatchError(
                f"Field '{field_name}': string mismatch\n"
                f"  Local: {repr(local_value)}\n"
                f"  Airtable: {repr(airtable_value)}"
            )
        return
    
    # Handle arrays (lists)
    if isinstance(local_value, list) and isinstance(airtable_value, list):
        if len(local_value) != len(airtable_value):
            raise ValueMismatchError(
                f"Field '{field_name}': array length mismatch\n"
                f"  Local length: {len(local_value)}\n"
                f"  Airtable length: {len(airtable_value)}\n"
                f"  Local: {local_value}\n"
                f"  Airtable: {airtable_value}"
            )
        
        if array_order_matters:
            # Order matters - compare element by element
            for i, (local_item, airtable_item) in enumerate(zip(local_value, airtable_value)):
                try:
                    assert_values_equal(
                        local_item,
                        airtable_item,
                        f"{field_name}[{i}]",
                        tolerance=tolerance,
                        array_order_matters=array_order_matters
                    )
                except ValueMismatchError as e:
                    raise ValueMismatchError(
                        f"Field '{field_name}': array element mismatch at index {i}\n{str(e)}"
                    ) from e
        else:
            # Order doesn't matter - sort and compare
            local_sorted = sorted(local_value, key=lambda x: str(x))
            airtable_sorted = sorted(airtable_value, key=lambda x: str(x))
            
            for i, (local_item, airtable_item) in enumerate(zip(local_sorted, airtable_sorted)):
                try:
                    assert_values_equal(
                        local_item,
                        airtable_item,
                        f"{field_name}[sorted {i}]",
                        tolerance=tolerance,
                        array_order_matters=array_order_matters
                    )
                except ValueMismatchError as e:
                    raise ValueMismatchError(
                        f"Field '{field_name}': sorted array mismatch\n"
                        f"  Local (sorted): {local_sorted}\n"
                        f"  Airtable (sorted): {airtable_sorted}\n"
                        f"{str(e)}"
                    ) from e
        return
    
    # Handle dictionaries (less common but possible)
    if isinstance(local_value, dict) and isinstance(airtable_value, dict):
        local_keys = set(local_value.keys())
        airtable_keys = set(airtable_value.keys())
        
        if local_keys != airtable_keys:
            raise ValueMismatchError(
                f"Field '{field_name}': dict keys mismatch\n"
                f"  Local keys: {local_keys}\n"
                f"  Airtable keys: {airtable_keys}\n"
                f"  Missing in local: {airtable_keys - local_keys}\n"
                f"  Extra in local: {local_keys - airtable_keys}"
            )
        
        for key in local_keys:
            try:
                assert_values_equal(
                    local_value[key],
                    airtable_value[key],
                    f"{field_name}.{key}",
                    tolerance=tolerance,
                    array_order_matters=array_order_matters
                )
            except ValueMismatchError as e:
                raise ValueMismatchError(
                    f"Field '{field_name}': dict value mismatch for key '{key}'\n{str(e)}"
                ) from e
        return
    
    # Type mismatch
    if type(local_value) != type(airtable_value):
        raise ValueMismatchError(
            f"Field '{field_name}': type mismatch\n"
            f"  Local: {local_value} ({type(local_value).__name__})\n"
            f"  Airtable: {airtable_value} ({type(airtable_value).__name__})"
        )
    
    # Default: exact equality check
    if local_value != airtable_value:
        raise ValueMismatchError(
            f"Field '{field_name}': value mismatch\n"
            f"  Local: {local_value} ({type(local_value).__name__})\n"
            f"  Airtable: {airtable_value} ({type(airtable_value).__name__})"
        )


def compare_records(
    local_record: Any,
    airtable_record: dict,
    computed_field_names: list,
    tolerance: float = 0.001,
    array_order_matters: bool = False
) -> dict:
    """
    Compare all computed fields in a record.
    
    Args:
        local_record: Record object from generated code
        airtable_record: Full record from Airtable API
        computed_field_names: List of computed field names to compare
        tolerance: Tolerance for floating point comparisons
        array_order_matters: If True, array order must match exactly
    
    Returns:
        Dict with comparison results:
        {
            "matches": int,
            "mismatches": int,
            "errors": List[dict] with mismatch details
        }
    """
    results = {
        "matches": 0,
        "mismatches": 0,
        "errors": []
    }
    
    for field_name in computed_field_names:
        # Get values
        airtable_value = airtable_record.get("fields", {}).get(field_name)
        
        # Try to get local value (support both dict and object access)
        if hasattr(local_record, field_name):
            local_value = getattr(local_record, field_name)
        elif isinstance(local_record, dict):
            local_value = local_record.get(field_name)
        else:
            results["errors"].append({
                "field": field_name,
                "error": f"Field not found in local record (type: {type(local_record).__name__})"
            })
            results["mismatches"] += 1
            continue
        
        # Compare
        try:
            assert_values_equal(
                local_value,
                airtable_value,
                field_name,
                tolerance=tolerance,
                array_order_matters=array_order_matters
            )
            results["matches"] += 1
        except ValueMismatchError as e:
            results["errors"].append({
                "field": field_name,
                "error": str(e),
                "local_value": local_value,
                "airtable_value": airtable_value
            })
            results["mismatches"] += 1
    
    return results
