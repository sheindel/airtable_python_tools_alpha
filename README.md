# Airtable Analysis Tools

A dual-environment Python application for analyzing Airtable bases with graph-based dependency mapping, formula analysis, and schema generation. Works as both a CLI tool and browser-based web application (no backend required).

## Features

### 📊 Analysis & Visualization
- **Dependency Mapping** - Visualize field relationships and dependencies as interactive flowcharts
- **Formula Compression** - Recursively inline helper fields into main formulas
- **Formula Evaluation** - Test formulas with sample data and see results
- **Complexity Scoring** - Identify complex fields and technical debt hotspots
- **Unused Fields Detection** - Find computed fields with no dependents

### 🔧 Schema & Code Generation
- **PostgreSQL Schema** - Export Airtable bases to SQL CREATE TABLE statements
- **TypeScript Types** - Generate type-safe interfaces for Airtable records
- **Code Generator** - Create SQL evaluation functions from formulas (experimental)

### 🌐 Dual Runtime
- **CLI Tools** - Server-side analysis with full Python stdlib
- **Web Application** - Browser-based PyScript app with zero backend infrastructure

## Quick Start

### Requirements
- Python ≥3.12 (CLI + web)
- Node.js ≥20 (web development only)
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/airtable_python_tools_alpha.git
cd airtable_python_tools_alpha

# Install Python dependencies
uv sync

# For web development: Install Node dependencies and build assets
npm install
npm run build
```

### Run Web Application

```bash
# Start local development server
uv run python main.py run-web
# Opens at http://localhost:8008
```

### Use CLI Tools

```bash
# View available commands
uv run python main.py --help

# Analyze dependencies
uv run python main.py dependency-map <base-id> <field-id>

# Compress a formula
uv run python main.py compress-formula <base-id> <field-id>

# Generate PostgreSQL schema
uv run python main.py generate-schema <base-id>

# Evaluate formula with test data
uv run python main.py evaluate-formula <base-id> <field-id>
```

## Web Application Usage

1. **Load Metadata**: Enter your Airtable Base ID and Personal Access Token
2. **Choose a Tool**: Navigate between tabs for different analysis types
3. **Analyze**: Select tables/fields and generate diagrams or reports
4. **Export**: Copy generated code, SQL, or Mermaid diagrams

All processing happens in your browser - metadata is stored in localStorage.

## CLI Usage

### Authentication

Create a `.env` file with your Airtable credentials:

```bash
AIRTABLE_API_KEY=your_personal_access_token
```

### Common Workflows

**Analyze field dependencies:**
```bash
uv run python main.py dependency-map appXXXXXXXXXXXXXX fldXXXXXXXXXXXXXX
```

**Compress nested formulas:**
```bash
uv run python main.py compress-formula appXXXXXXXXXXXXXX fldXXXXXXXXXXXXXX --depth 3
```

**Generate PostgreSQL schema:**
```bash
uv run python main.py generate-schema appXXXXXXXXXXXXXX --use-field-names > schema.sql
```

**Evaluate formula:**
```bash
uv run python main.py evaluate-formula appXXXXXXXXXXXXXX fldXXXXXXXXXXXXXX
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --group dev

# Install Node dependencies (for web development)
npm install

# Build assets
npm run build
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_at_metadata_graph.py -v

# Generate HTML coverage report
uv run pytest --cov=web --cov-report=html
open htmlcov/index.html

# Run performance benchmarks
uv run pytest tests/test_performance_benchmarks.py -v -s
```

### Frontend Development

```bash
# Watch mode for active development (CSS + TypeScript + server)
npm run dev

# Or run separately:
npm run watch:css  # Tailwind CSS compilation
npm run watch:ts   # TypeScript compilation
uv run python main.py run-web  # Development server
```

### Build Pipeline

The web application requires compiled CSS and TypeScript:

```bash
# Build everything (required before deploying)
npm run build

# Or separately:
npm run build:css  # Compile Tailwind CSS to web/output.css
npm run build:ts   # Compile TypeScript to web/modules/*.js
```

### Project Structure

```
.
├── main.py                      # CLI entry point
├── pyproject.toml               # Python dependencies
├── package.json                 # Node.js dependencies
├── web/                         # Web application
│   ├── index.html               # Entry point
│   ├── main.py                  # Tab coordinator
│   ├── tabs/                    # Feature modules
│   ├── components/              # Shared utilities
│   └── src/                     # TypeScript sources
├── tests/                       # Unit & integration tests
├── scripts/                     # Build & debug tools
└── docs/                        # Documentation
```

## Architecture

This project uses a **dual-architecture pattern** where core analysis modules are written once and run in two environments:

1. **CLI Environment** - Standard Python with full stdlib, httpx for API calls
2. **Web Environment** - PyScript (Python-in-browser) with limited stdlib

Both share:
- [NetworkX](https://networkx.org/) for graph-based dependency analysis
- Core modules: `at_metadata_graph.py`, `airtable_mermaid_generator.py`
- Analysis algorithms: formula compression, complexity scoring, dependency traversal

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Testing

The project includes comprehensive test coverage:

- **Unit Tests** - Core business logic (80%+ coverage goal)
- **Integration Tests** - End-to-end CLI workflows
- **Performance Benchmarks** - Track code generation speed
- **Web Tests** - Chrome MCP-based browser testing

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Documentation

- [docs/architecture.md](docs/architecture.md) - System architecture and design patterns
- [docs/testing-guide.md](docs/testing-guide.md) - Testing strategy and procedures
- [docs/ai-testing-guide.md](docs/ai-testing-guide.md) - AI-assisted regression testing
- [tests/README.md](tests/README.md) - Test suite overview
- [web/README.md](web/README.md) - Web application guide
- [web/TYPESCRIPT.md](web/TYPESCRIPT.md) - TypeScript development

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `uv run pytest`
4. Build assets: `npm run build`
5. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Related Projects

- [PyScript](https://pyscript.net/) - Python in the browser
- [NetworkX](https://networkx.org/) - Graph analysis library
- [Airtable](https://airtable.com/) - Collaborative database platform
