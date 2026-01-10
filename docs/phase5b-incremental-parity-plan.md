# Phase 5B: Advanced Parity Tests - Implementation Plan

**Status**: 🚧 In Progress  
**Start Date**: January 9, 2026  
**Related**: [formula-evaluator-incremental-design.md](formula-evaluator-incremental-design.md)

## Overview

Phase 5B implements advanced parity testing that validates generated formula evaluators produce **identical results** to Airtable's own calculations by comparing against live Airtable data.

## Current Status

### ✅ Already Implemented (Foundation)

1. **Helper Modules** - All helper functions working:
   - `tests/helpers/airtable_api.py` - API interaction
     - `fetch_schema_cached()` ✅
     - `get_random_record_id()` ✅
     - `fetch_record()` ✅
     - `extract_raw_fields()` ✅
     - `get_computed_field_names()` ✅
   
   - `tests/helpers/comparison.py` - Value comparison
     - `assert_values_equal()` ✅
     - `compare_records()` ✅
     - Support for numbers, strings, arrays, booleans, nulls ✅

2. **Test Infrastructure**:
   - Test file structure in place
   - Fixtures for credentials and schema
   - Basic test cases sketched out
   - 6/6 helper utility tests passing

3. **Quick Test Script**:
   - `test_parity_quick.py` - Manual testing script
   - Successfully fetches data and generates evaluators
   - Shows 11 matches / 11 mismatches on sample data
   - Demonstrates end-to-end flow works

### 🔧 Issues Found

From `test_parity_quick.py` results:
- Formula fields returning `None` instead of computed values
- Possible issues:
  1. Formula parsing/transpilation errors
  2. Field reference resolution problems
  3. Missing function implementations
  4. Data access mode issues (dict vs dataclass)

### 📋 Phase 5B Remaining Tasks

#### Task 1: Debug Formula Computation 🔴
**Priority**: HIGH  
**Status**: BLOCKED BY BUG #3

**Bugs Found & Fixed**:

##### Bug #1: Table Filtering ⚠️ CRITICAL - ✅ FIXED
**File**: `web/code_generators/incremental_runtime_generator.py` (line ~140)

**Problem**: `field_info_dict.get("table_id")` always None - dict only has "table_name"

**Fix**: Look up table_id from table_name in metadata

**Impact**: 0 fields → 22 fields generated ✅

##### Bug #2: Field Name Mismatch ⚠️ HIGH - ✅ FIXED
**Problem**: Generated code expects snake_case (`first_name`), raw data has original names (`First Name`)

**Fix**: Added `to_snake_case()` and `convert_record_to_snake_case()` helpers in `tests/helpers/airtable_api.py`

**Impact**: Arithmetic formulas now work. Test results: 3 matches (rollups/counts), 19 mismatches (string formulas)

##### Bug #3: Formula Transpilation Broken ⚠️ CRITICAL - ✅ FIXED
**File**: `web/code_generators/python_runtime_generator.py` (PythonFormulaTranspiler)

**Problem**: String concatenation formulas generated completely malformed Python code with broken nested ternaries

**Root Cause**: `_transpile_binary_op()` was double-wrapping already-transpiled expressions with null checks

**Fix**: Added `_ensure_string()` method that only wraps field references and function calls, not literals or already-safe BinaryOp expressions

**Impact**: String concatenation now works. Formula code reduced from 319 chars (broken) to 153 chars (correct) ✅

**Status**: ✅ FIXED (January 9, 2026)

##### Bug #4: Overly Aggressive Null Safety Checks ⚠️ HIGH - ✅ FIXED
**File**: `web/code_generators/incremental_runtime_generator.py` (line ~450)

**Problem**: Generated code had upfront null checks that returned None if ANY dependency was None, preventing formulas from handling None values themselves

**Fix**: Disabled upfront null checks for formula fields (kept for lookups/rollups). Formula code already has appropriate null handling.

**Impact**: Formulas can now handle None inputs correctly (e.g., None + " " + "Doe" = " Doe")

**Status**: ✅ FIXED (January 9, 2026)

##### Bug #5: Missing Fields in Raw Data ⚠️ HIGH - ✅ FIXED
**File**: `tests/helpers/airtable_api.py` (extract_raw_fields)

**Problem**: Airtable API doesn't include empty/None fields in responses, causing KeyErrors when formulas accessed them

**Fix**: Updated `extract_raw_fields()` to initialize ALL raw fields with None before filling in actual values

**Impact**: No more KeyErrors. Tests run to completion.

**Status**: ✅ FIXED (January 9, 2026)

---

### 📊 Current Test Results (January 9, 2026)

Running `test_parity_quick.py` shows:
- **Before fixes**: All formulas returned None, 1/22 matches (5%)
- **After fixes**: Simple formulas work, 3-6/22 matches (14-27%)
- **Remaining issues**: Lookups/rollups return empty arrays (need DataAccess implementation)

---

**Blocking Decision Required**:
1. **Option A**: DONE - Transpiler is now fixed! ✅
2. **Option B**: Not needed - all formula types can be tested
3. **Option C**: Not needed - fix is sustainable

**Deliverable**: ✅ Working formula transpilation for `&` operator and other operations

#### Task 2: Improve Error Reporting ⏳
**Priority**: HIGH  
**Blockers**: None

Steps:
1. Catch and log formula evaluation exceptions
2. Add field-level error reporting
3. Show which formulas failed vs succeeded
4. Include formula text in error messages

**Deliverable**: Clear error messages for formula failures

#### Task 3: Implement Lookup Field Tests ⏳
**Priority**: MEDIUM  
**Blockers**: Task 1

Steps:
1. Test single-value lookups
2. Test multi-value lookups  
3. Handle missing linked records
4. Test with actual related data

**Test**: `test_lookup_field_parity()`

#### Task 4: Implement Rollup Field Tests ⏳
**Priority**: MEDIUM  
**Blockers**: Task 1, Task 3

Steps:
1. Test SUM aggregations
2. Test COUNT aggregations
3. Test other aggregations (AVG, MAX, MIN)
4. Handle empty arrays
5. Test with actual related data

**Test**: `test_rollup_field_parity()`

#### Task 5: Implement Nested Formula Tests ⏳
**Priority**: MEDIUM  
**Blockers**: Task 1

Steps:
1. Test formula → formula dependencies
2. Test depth 2+ formulas
3. Verify computation order
4. Test cascading updates

**Test**: `test_nested_formula_parity()`

#### Task 6: Implement Edge Case Tests ⏳
**Priority**: LOW  
**Blockers**: Task 1

Steps:
1. Test null value handling
2. Test empty strings
3. Test division by zero
4. Test type coercion edge cases
5. Test array operations

**Test**: `test_edge_cases_parity()`

#### Task 7: Improve Statistical Sampling ⏳
**Priority**: LOW  
**Blockers**: Task 1-6

Steps:
1. Fix `test_statistical_sampling()` to run properly
2. Add configurable sample sizes
3. Add table-specific sampling
4. Generate statistical reports
5. Set pass/fail thresholds

**Test**: `test_statistical_sampling()` - Currently passing but needs refinement

#### Task 8: Documentation & Reporting ⏳
**Priority**: LOW  
**Blockers**: Task 1-7

Steps:
1. Create Phase 5B completion document
2. Document findings and limitations
3. Create troubleshooting guide
4. Add usage examples
5. Update main README

**Deliverable**: Complete Phase 5B documentation

## Success Criteria

### Minimum Viable Success (MVP)
- [ ] Simple formula fields match Airtable (string concat, arithmetic)
- [ ] Error reporting shows clear failure reasons
- [ ] At least 1 table passes 80%+ parity test
- [ ] Documentation explains how to run tests

### Full Success
- [ ] All formula types tested (formula, lookup, rollup, count)
- [ ] Edge cases covered (nulls, errors, type coercion)
- [ ] Statistical sampling shows >80% success rate across tables
- [ ] Nested formulas work correctly
- [ ] Clear documentation and examples
- [ ] Automated CI integration possible

## Testing Approach

### Phase 1: Fix Basic Formulas
Focus on simplest formulas first:
1. String concatenation: `{First Name} & " " & {Last Name}`
2. Simple arithmetic: `{Quantity} * {Price}`
3. Comparison: `{Amount} > 100`

### Phase 2: Add Complexity
Once basics work:
1. IF statements: `IF({Active}, "Yes", "No")`
2. String functions: `UPPER({Name})`
3. Math functions: `ROUND({Amount}, 2)`

### Phase 3: Lookups & Rollups
Requires linked record support:
1. Implement DataAccess interface
2. Mock or fetch related records
3. Test lookup operations
4. Test rollup aggregations

### Phase 4: Edge Cases & Validation
Final validation:
1. Test error conditions
2. Test null handling
3. Test type edge cases
4. Statistical sampling

## Known Limitations

### Current Implementation Gaps
1. **Lookup/Rollup Support**: Generated code needs DataAccess implementation with actual data
2. **Field References**: Some formula parsing issues may exist
3. **Function Coverage**: Not all Airtable functions implemented
4. **Type Coercion**: May differ from Airtable in edge cases

### Testing Limitations
1. **API Rate Limits**: Airtable has rate limits (5 requests/second)
2. **Data Freshness**: Cached schema may be stale
3. **Random Sampling**: May miss rare edge cases
4. **Live Data**: Tests depend on external API availability

### Acceptable Failures
Some mismatches are expected:
- Unsupported functions → Document in limitations
- Precision differences → Accept with tolerance
- Date format differences → Normalize before comparison
- Missing linked records → Document data requirements

## Timeline

**Estimated Total Time**: 4-6 hours

- Task 1 (Debug Formulas): 1-2 hours
- Task 2 (Error Reporting): 30 minutes
- Tasks 3-6 (Test Implementation): 2-3 hours
- Task 7 (Statistical Sampling): 30 minutes
- Task 8 (Documentation): 30-60 minutes

## Next Steps

**Immediate**: Start with Task 1 - Debug why formulas return None

1. Add logging to generated `update_record()` function
2. Check COMPUTATION_GRAPH data structure
3. Verify formula fields are in FIELD_COMPUTERS mapping
4. Test with simplest possible formula
5. Fix root cause

**After Task 1**: Proceed with Tasks 2-8 in order

## Resources

- **Test File**: `tests/test_formula_parity.py`
- **Helpers**: `tests/helpers/airtable_api.py`, `tests/helpers/comparison.py`
- **Quick Test**: `test_parity_quick.py`
- **Generator**: `web/code_generators/incremental_runtime_generator.py`
- **Design Doc**: `docs/formula-evaluator-incremental-design.md`

## Progress Tracking

- [x] Phase 5B plan document created
- [x] Task 1a: Debug formula computation - **ROOT CAUSE FOUND**
  - [x] Fixed table filtering bug in `build_computation_graph()`
  - [x] Identified field name mismatch (snake_case vs original names)
  - [ ] Implement field name conversion in parity tests
- [ ] Task 1b: Fix formula transpilation issues
- [ ] Task 2: Improve error reporting
- [ ] Task 3: Lookup field tests
- [ ] Task 4: Rollup field tests
- [ ] Task 5: Nested formula tests
- [ ] Task 6: Edge case tests
- [ ] Task 7: Statistical sampling
- [ ] Task 8: Documentation

## Bugs Fixed

### Bug #1: Table Filtering ✅ FIXED
**File**: `web/code_generators/incremental_runtime_generator.py`  
**Line**: ~140  
**Problem**: Checked for non-existent `field_info_dict.get("table_id")` which was always None  
**Solution**: Look up table_id from table_name in metadata  
**Impact**: Generated evaluators now include all 22 computed fields (was 0 before)

### Bug #2: Field Name Mismatch 🔧 IN PROGRESS
**Files**: `tests/test_formula_parity.py`, `test_parity_quick.py`  
**Problem**: Generated code uses snake_case (`first_name`) but Airtable records use original names (`First Name`)  
**Solution**: Convert field names to snake_case before passing to evaluator  
**Status**: Implementing fix

---

**Status**: 🚧 Task 1 In Progress - Major breakthrough!  
**Date**: January 9, 2026  
**Next**: Implement field name conversion
