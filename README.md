# Airtable Analysis Tools

Python tools for analyzing Airtable bases with both CLI and web interfaces.

## Features

- **Dependency Mapping**: Visualize field relationships and dependencies
- **Formula Analysis**: Compress, evaluate, and graph formulas
- **Complexity Scoring**: Identify complex fields and technical debt
- **Schema Generation**: Export to PostgreSQL and TypeScript types
- **Unused Fields Detection**: Find fields with no dependents

## Quick Start

**Requirements**: Python ≥3.12, Node.js (for build pipeline)

```bash
# Install dependencies
uv sync
npm install

# Build CSS and TypeScript (required before running web app)
npm run build

# Run web application
uv run python main.py run-web

# Or use CLI commands
uv run python main.py --help
```

## CLI Commands

```bash
# Generate dependency diagram
uv run python main.py dependency-map <base-id> <field-id>

# Compress formulas
uv run python main.py compress-formula <base-id> <field-id>

# Generate PostgreSQL schema
uv run python main.py generate-schema <base-id>

# Evaluate formula with test data
uv run python main.py evaluate-formula <base-id> <field-id>
```

## Development

```bash
# Run tests with coverage
uv run pytest --cov=web --cov-report=html

# Watch CSS and TypeScript for changes
npm run watch

# Generate PyScript config
uv run python scripts/generate_pyscript_config.py
```

See [web/TYPESCRIPT.md](web/TYPESCRIPT.md) for TypeScript development details.

## License

MIT License - See [LICENSE](LICENSE) file for details.

