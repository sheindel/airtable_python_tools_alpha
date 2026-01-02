# TypeScript Setup

This project uses TypeScript for all JavaScript code to improve type safety, especially for the PyScript/JavaScript interface.

## Directory Structure

```
web/
├── src/                    # TypeScript source files
│   ├── types/
│   │   ├── pyscript.d.ts  # PyScript interface types
│   │   └── dom.d.ts       # Custom web component types
│   ├── modules/           # Module TypeScript files (to be converted)
│   ├── components/
│   │   └── ui/            # Web component TypeScript files (to be converted)
│   └── script.ts          # Main entry point (to be converted)
├── dist/                   # Compiled JavaScript output (gitignored)
│   ├── *.js               # Compiled JS files
│   ├── *.js.map           # Source maps for debugging
│   ├── *.d.ts             # Type declarations
│   └── *.d.ts.map         # Declaration source maps
├── *.py                    # Python modules (unchanged)
├── index.html              # Main HTML (will reference dist/*.js)
└── pyscript.toml           # PyScript configuration
```

## Building

### Development Mode (Watch)

```bash
# Watch both CSS and TypeScript (recommended)
npm run watch

# Or separately:
npm run watch:css  # Tailwind CSS watcher
npm run watch:ts   # TypeScript compiler watcher
```

### Production Build

```bash
# Build both CSS and TypeScript
npm run build

# Or separately:
npm run build:css  # Build Tailwind CSS
npm run build:ts   # Compile TypeScript
```

## Type Definitions

### PyScript Interface Types

[web/src/types/pyscript.d.ts](web/src/types/pyscript.d.ts) defines all Python functions exposed to JavaScript via `window.functionName`. This provides:

- **Type safety** for all PyScript function calls
- **Autocomplete** in IDEs for Python functions
- **Compile-time errors** if calling non-existent functions or wrong parameters

Example:
```typescript
// TypeScript knows this function exists and its signature
window.compressFormulaFromUI(
  tableName,      // string
  fieldName,      // string
  depth,          // number | null
  'field_ids',    // 'field_ids' | 'field_names'
  'compact'       // 'compact' | 'logical'
);
```

### Custom Web Component Types

[web/src/types/dom.d.ts](web/src/types/dom.d.ts) defines custom HTML elements like `<at-dropdown>`, `<at-tab-manager>`, etc.

Example:
```typescript
const dropdown = document.getElementById('my-dropdown') as AtDropdownElement;
dropdown.options = [...];  // TypeScript knows this property exists
dropdown.clear();          // TypeScript knows this method exists
```

## TypeScript Configuration

[tsconfig.json](../tsconfig.json) is configured for:
- **Target:** ES2020 (modern browsers)
- **Module:** ES2020 (native ES modules)
- **Strict mode:** Enabled (maximum type safety)
- **Source maps:** Enabled (for debugging)
- **Declarations:** Enabled (for other TypeScript consumers)

## Migration Status

### Phase 1: Setup & Foundation ✅ COMPLETE
- TypeScript compiler configured
- Type definitions created
- Build pipeline integrated
- Directory structure established

### Phase 2: Convert Utility Modules (Next)
- [ ] `modules/dom-utils.js` → `src/modules/dom-utils.ts`
- [ ] `modules/toast.js` → `src/modules/toast.ts`
- [ ] `components/ui/schema-store.js` → `src/components/ui/schema-store.ts`

### Phase 3: Convert Web Components
- [ ] `components/ui/at-dropdown.js` → `src/components/ui/at-dropdown.ts`
- [ ] `components/ui/tab-manager.js` → `src/components/ui/tab-manager.ts`
- [ ] `components/ui/theme-toggle.js` → `src/components/ui/theme-toggle.ts`

### Phase 4: Convert Tab Modules
- [ ] `modules/compressor.js` → `src/modules/compressor.ts`
- [ ] `modules/grapher.js` → `src/modules/grapher.ts`
- [ ] `modules/scorecard.js` → `src/modules/scorecard.ts`
- [ ] `modules/table-analysis.js` → `src/modules/table-analysis.ts`
- [ ] `modules/unused.js` → `src/modules/unused.ts`
- [ ] `modules/action-handlers.js` → `src/modules/action-handlers.ts`
- [ ] `modules/mermaid-actions.js` → `src/modules/mermaid-actions.ts`
- [ ] `modules/ui-events.js` → `src/modules/ui-events.ts`

### Phase 5: Convert Main Entry Point
- [ ] `script.js` → `src/script.ts`

### Phase 6: Update HTML References
- [ ] Update `index.html` to use compiled JS from `dist/`

## Benefits

### 1. Type Safety for PyScript Interface
Compile-time checking ensures correct usage of Python functions called from JavaScript.

### 2. Better IDE Support
Full autocomplete, go-to-definition, and refactoring support.

### 3. Null Safety
Explicit handling of potentially null/undefined values.

### 4. Self-Documenting Code
Types serve as inline documentation.

### 5. AI-Friendly
AI tools can better understand and work with typed code.

## Troubleshooting

### "Cannot find module" errors
Make sure you're importing with correct paths relative to `web/src/`:
```typescript
import { getDropdown } from './modules/dom-utils';  // ✓ Correct
import { getDropdown } from '../modules/dom-utils'; // ✗ Wrong
```

### Compilation errors in CI/CD
GitHub Actions workflow automatically runs `npm run build` which includes TypeScript compilation.

### Source maps not working in browser
Ensure dev tools are configured to use source maps. The compiled JS includes `//# sourceMappingURL` comments.

### TypeScript not catching errors
Check that strict mode is enabled in `tsconfig.json` and you're using explicit types (not `any`).

## Adding New TypeScript Files

1. Create `.ts` file in `web/src/`
2. Import types as needed from `./types/`
3. Run `npm run build:ts` to compile
4. Reference compiled JS from HTML: `<script src="./dist/yourfile.js">`

## Resources

- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [TypeScript Configuration Reference](https://www.typescriptlang.org/tsconfig)
- [PyScript Documentation](https://pyscript.net/)
