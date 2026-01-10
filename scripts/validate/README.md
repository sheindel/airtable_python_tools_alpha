# Validation Tools

Interactive validation tools for checking parity and correctness of generated code.

## Coming Soon

These tools are planned for future implementation:

### check_parity.py (Planned)
Interactive tool to verify formula evaluation parity between Airtable and local evaluators.

**Planned Usage:**
```bash
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX

# Check specific table
uv run python scripts/validate/check_parity.py --table Contacts

# Check all tables
uv run python scripts/validate/check_parity.py --all

# Save detailed report
uv run python scripts/validate/check_parity.py \
  --table Contacts \
  --report parity_report.json
```

**Planned Features:**
- Compare all computed fields in a table
- Test with multiple records
- Generate detailed mismatch reports
- Export results as JSON/CSV

### verify_sql.py (Planned)
Verify SQL generation against test cases.

### verify_typescript.py (Planned)
Verify TypeScript type generation.

## Current Alternatives

For now, use:
- **Integration tests**: `uv run pytest tests/test_integration_parity.py --airtable-live`
- **Debug tools**: `uv run python scripts/debug/inspect_formula.py` for single-field validation

See [../../tests/README.md](../../tests/README.md) for more details.
