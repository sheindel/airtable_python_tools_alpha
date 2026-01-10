# Development Scripts

This directory contains development and debugging tools for the Airtable Analysis Tools project.

## Directory Structure

```
scripts/
├── debug/          # Inspection tools for AST, graphs, evaluators
├── validate/       # Validation and parity checking tools (planned)
└── generate_pyscript_config.py  # PyScript config generator
```

## Quick Start

### Debug Tools

Inspect formula AST:
```bash
uv run python scripts/debug/inspect_ast.py 'IF({fldA}, "Yes", "No")'
```

Inspect computation graph:
```bash
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
uv run python scripts/debug/inspect_graph.py --table Contacts
```

Debug a specific formula field:
```bash
uv run python scripts/debug/inspect_formula.py --table Contacts --field Name
```

See [debug/README.md](debug/README.md) for complete documentation.

### Build Tools

Generate PyScript configuration:
```bash
uv run python scripts/generate_pyscript_config.py
```

This auto-discovers Python files in `web/` and updates `web/pyscript.toml`.

## Tool Categories

### Inspection Tools (debug/)
- **inspect_ast.py** - View formula AST structure
- **inspect_graph.py** - View computation graph
- **inspect_evaluator.py** - Generate and view evaluator code
- **inspect_transpiler.py** - View transpiler output
- **inspect_formula.py** - Debug specific formula fields

### Validation Tools (validate/)
- Coming soon: Interactive parity checking
- For now, use: `pytest tests/test_integration_parity.py --airtable-live`

### Build Tools (root)
- **generate_pyscript_config.py** - Auto-generate PyScript file mappings

## When to Use These Tools

### Use Debug Tools When:
- Formula not computing correctly
- Need to understand AST structure
- Investigating computation graph issues
- Comparing local vs. Airtable values
- Developing new formula features

### Use Integration Tests Instead When:
- Running automated checks
- CI/CD validation
- Regression testing
- Coverage measurement

## Environment Setup

Most tools require Airtable credentials:

```bash
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
```

**Tip:** Add these to your `~/.zshrc` or `~/.bashrc` for persistence.

## Integration with Main CLI

Some debug functionality may be added to the main CLI in future:

```bash
# Planned
uv run python main.py debug-formula '{field}'
uv run python main.py verify-parity --table Contacts
```

For now, use scripts directly.

## Contributing

When adding new scripts:

1. Place in appropriate subdirectory (debug/ or validate/)
2. Add shebang: `#!/usr/bin/env python3`
3. Include docstring with usage examples
4. Accept credentials via env vars or CLI args
5. Update relevant README.md
6. Add entry to this main README

## Related Documentation

- [tests/README.md](../tests/README.md) - Automated test suite
- [TESTING_REORGANIZATION.md](../TESTING_REORGANIZATION.md) - Overall testing strategy
- [web/](../web/) - Web application source
- [docs/](../docs/) - Architecture and design docs
