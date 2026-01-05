# Airtable Analysis Tools

Python tools for analyzing Airtable bases with both CLI and web interfaces.

## Features

- **Dependency Mapping**: Visualize field relationships and dependencies
- **Formula Analysis**: Compress, evaluate, and graph formulas
- **Complexity Scoring**: Identify complex fields and technical debt
- **Schema Generation**: Export to PostgreSQL and TypeScript types
- **Unused Fields Detection**: Find fields with no dependents

## Installation & Setup

This repository supports three usage scenarios:

### 1. Python CLI Only

If you only need the command-line tools:

```bash
# Install Python dependencies (requires Python ≥3.12)
uv sync

# Run CLI commands
uv run python main.py --help
```

### 2. Web App Only

If you only need to build/deploy the web interface:

```bash
# Install Node dependencies (requires Node.js ≥20)
npm install

# Build CSS and TypeScript
npm run build

# Generate PyScript config
uv sync
uv run python scripts/generate_pyscript_config.py
```

### 3. Full Development Environment

For development on both CLI and web:

```bash
### Python Development

```bash
# Run tests with coverage
uv run pytest --cov=web --cov-report=html

# Install dev dependencies
uv sync --group dev

# Generate PyScript config (auto-discovers .py files)
uv run python scripts/generate_pyscript_config.py
```

### Frontend Development

```bash
# Watch CSS and TypeScript for changes (runs both in parallel)
npm run watch

# Or separately:
npm run watch:css  # Tailwind CSS
npm run watch:ts   # TypeScript compilation

# Full dev mode (CSS + TS + web server)
npm run dev
```

### Build Pipeline

The web application requires building both CSS and TypeScript:

```bash
# Build everything (required before deploying)
npm run build

# Or separately:
npm run build:css  # Compile Tailwind CSS to web/output.css
npm run build:ts   # Compile TypeScript to web/modules/*.js

# Or use watch mode for active development
npm run dev  # Runs watch:css, watch:ts, and web server
```

## Quick Start

**Requirements**: Python ≥3.12 (CLI/web), Node.js ≥20 (web only)

```bash
# Full setup
uv sync && npm install && npm run build

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

# Run performance benchmarks
uv run pytest tests/test_performance_benchmarks.py -v -s

# Run benchmarks with external schema
BENCHMARK_SCHEMA=/path/to/schema.json uv run pytest tests/test_performance_benchmarks.py -v

# Watch CSS and TypeScript for changes
npm run watch

# Generate PyScript config
uv run python scripts/generate_pyscript_config.py
```

### Performance Testing

The project includes performance benchmarks to track code generation speed:

```bash
# Run all benchmarks (uses default demo schema)
uv run pytest tests/test_performance_benchmarks.py -v -s

# Use a custom schema for benchmarking
BENCHMARK_SCHEMA=/path/to/large-schema.json uv run pytest tests/test_performance_benchmarks.py -v

# Or place schemas in tests/schemas/ directory (gitignored)
# Files like tests/schemas/benchmark.json are automatically detected
```

**External Schemas**: To test with large, real-world schemas without committing them:
1. Place schema JSON files in `tests/schemas/` (directory is gitignored)
2. Or set environment variable: `SCHEMA_PATH=/path/to/schema.json`
3. See [tests/schemas/README.md](tests/schemas/README.md) for details

See [web/TYPESCRIPT.md](web/TYPESCRIPT.md) for TypeScript development details.

## License

MIT License - See [LICENSE](LICENSE) file for details.

