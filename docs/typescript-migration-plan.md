# TypeScript Migration Plan

## Overview

This document outlines the plan to migrate the JavaScript codebase to TypeScript. Since we already have an npm build pipeline for Tailwind CSS, adding TypeScript compilation is a natural extension that will:

1. **Improve PyScript/JavaScript interface resilience** through type safety
2. **Make future AI-assisted development cleaner** with better type inference
3. **Catch errors at build time** rather than runtime
4. **Provide better IDE support** with autocomplete and inline documentation

## Current JavaScript Codebase

### File Inventory (16 JS files total)

**Core Application:**
- `web/script.js` (~400 lines) - Main entry point, orchestration

**Modules (10 files):**
- `web/modules/action-handlers.js` - Action routing
- `web/modules/compressor.js` (~160 lines) - Formula compression UI
- `web/modules/dom-utils.js` (~80 lines) - DOM utilities, clipboard, time formatting
- `web/modules/grapher.js` - Field graphing UI
- `web/modules/mermaid-actions.js` - Mermaid diagram interactions
- `web/modules/scorecard.js` - Complexity scorecard UI
- `web/modules/table-analysis.js` - Table analysis UI
- `web/modules/toast.js` - Toast notification wrapper
- `web/modules/ui-events.js` - Event wiring
- `web/modules/unused.js` - Unused fields UI

**Web Components (4 files):**
- `web/components/ui/at-dropdown.js` (~200 lines) - Custom dropdown component
- `web/components/ui/schema-store.js` (~50 lines) - LocalStorage abstraction
- `web/components/ui/tab-manager.js` - Tab navigation component
- `web/components/ui/theme-toggle.js` - Dark mode toggle

**Build Config:**
- `tailwind.config.js` - Tailwind configuration (keep as JS)

## TypeScript Setup Required

### 1. Dependencies

```json
{
  "devDependencies": {
    "tailwindcss": "^3.4.17",
    "typescript": "^5.3.3",
    "@types/node": "^20.0.0"
  }
}
```

### 2. TypeScript Configuration (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ES2020",
    "lib": ["ES2020", "DOM"],
    "moduleResolution": "node",
    "allowJs": true,
    "checkJs": false,
    "outDir": "./web/dist",
    "rootDir": "./web",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": [
    "web/**/*.ts",
    "web/**/*.js"
  ],
  "exclude": [
    "node_modules",
    "web/dist",
    "**/*.py"
  ]
}
```

### 3. Build Scripts Update (`package.json`)

```json
{
  "scripts": {
    "build:css": "tailwindcss -i ./web/input.css -o ./web/output.css --minify",
    "watch:css": "tailwindcss -i ./web/input.css -o ./web/output.css --watch",
    "build:ts": "tsc",
    "watch:ts": "tsc --watch",
    "build": "npm run build:css && npm run build:ts",
    "watch": "npm run watch:css & npm run watch:ts",
    "dev": "npm run watch"
  }
}
```

### 4. Output Structure

```
web/
├── src/           (new - TypeScript source files)
│   ├── script.ts
│   ├── modules/
│   └── components/
├── dist/          (new - compiled JavaScript)
│   ├── script.js
│   ├── script.js.map
│   ├── modules/
│   └── components/
├── *.py           (unchanged - Python modules)
└── index.html     (update script imports to dist/)
```

## Type Definitions for PyScript Interface

This is the **critical improvement** for AI development and runtime safety.

### `web/src/types/pyscript.d.ts`

```typescript
/**
 * Type definitions for PyScript global functions exposed from Python
 */

// Airtable metadata types
interface AirtableField {
  id: string;
  name: string;
  type: string;
  options?: {
    formula?: string;
    referencedFieldIds?: string[];
    [key: string]: any;
  };
}

interface AirtableTable {
  id: string;
  name: string;
  fields: AirtableField[];
}

interface AirtableMetadata {
  tables: AirtableTable[];
}

interface SchemaPayload {
  version: number;
  timestamp: string;
  schema: AirtableMetadata;
}

// Dropdown option structure
interface DropdownOption {
  id: string;
  text: string;
  tableId?: string;
  tableName?: string;
  formula?: string;
  table?: AirtableTable;
}

// PyScript exposed functions (from Python to JS via window.functionName)
declare global {
  interface Window {
    // Dependency Mapper Tab
    parametersChanged(): void;
    updateMermaidGraph(tableId: string, fieldId: string, flowchartType: string): void;
    
    // Formula Compressor Tab
    compressFormulaFromUI(
      tableName: string,
      fieldName: string,
      compressionDepth: number | null,
      outputFormat: 'field_ids' | 'field_names',
      displayFormat: 'compact' | 'logical'
    ): void;
    generateTableReportData(tableName: string, compressionDepth: number | null): string;
    convertFormulaDisplay(formula: string, outputFormat: 'field_ids' | 'field_names'): string;
    formatFormulaCompact(formula: string): string;
    formatFormulaLogical(formula: string): string;
    
    // Formula Evaluator Tab
    loadFieldDependencies(): void;
    evaluateFormulaWithValues(
      fieldId: string,
      dependencies: Record<string, any>,
      outputFormat: 'field_ids' | 'field_names'
    ): void;
  }
}

export {};
```

### `web/src/types/dom.d.ts`

```typescript
/**
 * Type definitions for custom web components
 */

interface AtDropdownElement extends HTMLElement {
  options: DropdownOption[];
  value: string;
  selectedId: string | null;
  selectedOption: DropdownOption | null;
  clear(): void;
  open(): void;
  close(): void;
  selectById(optionId: string): void;
}

interface AtTabManagerElement extends HTMLElement {
  setActive(tabName: string, emit?: boolean): void;
}

interface AtThemeToggleElement extends HTMLElement {
  // Theme toggle methods (if any)
}

declare global {
  interface HTMLElementTagNameMap {
    'at-dropdown': AtDropdownElement;
    'at-tab-manager': AtTabManagerElement;
    'at-theme-toggle': AtThemeToggleElement;
  }
}

export {};
```

## Migration Strategy

### Phase 1: Setup & Foundation (Day 1)
✅ **Low Risk**

1. Install TypeScript dependencies
2. Create `tsconfig.json`
3. Create type definition files (`pyscript.d.ts`, `dom.d.ts`)
4. Update build scripts
5. Test build pipeline

**Deliverable:** TypeScript compiles successfully (even with no TS files yet)

### Phase 2: Convert Utility Modules (Day 1-2)
✅ **Low Risk** - No PyScript dependencies

1. `web/modules/dom-utils.js` → `web/src/modules/dom-utils.ts`
2. `web/modules/toast.js` → `web/src/modules/toast.ts`
3. `web/components/ui/schema-store.js` → `web/src/components/ui/schema-store.ts`

**Benefits:**
- Pure utility functions, easy to type
- Immediate value from type checking
- Build familiarity with migration process

### Phase 3: Convert Web Components (Day 2-3)
⚠️ **Medium Risk** - DOM APIs, event handling

1. `web/components/ui/at-dropdown.js` → `web/src/components/ui/at-dropdown.ts`
2. `web/components/ui/tab-manager.js` → `web/src/components/ui/tab-manager.ts`
3. `web/components/ui/theme-toggle.js` → `web/src/components/ui/theme-toggle.ts`

**Benefits:**
- Type-safe custom element interfaces
- Better event typing (CustomEvent<T>)
- Generic parameter support for options

### Phase 4: Convert Tab Modules (Day 3-4)
⚠️ **Medium Risk** - PyScript interface calls

1. `web/modules/compressor.js` → `web/src/modules/compressor.ts`
2. `web/modules/grapher.js` → `web/src/modules/grapher.ts`
3. `web/modules/scorecard.js` → `web/src/modules/scorecard.ts`
4. `web/modules/table-analysis.js` → `web/src/modules/table-analysis.ts`
5. `web/modules/unused.js` → `web/src/modules/unused.ts`
6. `web/modules/action-handlers.js` → `web/src/modules/action-handlers.ts`
7. `web/modules/mermaid-actions.js` → `web/src/modules/mermaid-actions.ts`
8. `web/modules/ui-events.js` → `web/src/modules/ui-events.ts`

**Benefits:**
- Type-safe PyScript function calls
- Null safety for DOM element access
- Parameter validation at compile time

### Phase 5: Convert Main Entry Point (Day 4)
⚠️ **Medium Risk** - Orchestrates everything

1. `web/script.js` → `web/src/script.ts`

**Benefits:**
- Complete type coverage across entire app
- Type-checked event listeners
- Safe localStorage access

### Phase 6: Update HTML & Deployment (Day 5)
✅ **Final Integration**

1. Update `web/index.html` script imports
2. Update `.gitignore` for `web/dist/`
3. Update GitHub Actions workflow
4. Update documentation

## Example Conversions

### Before: `web/modules/dom-utils.js`

```javascript
export function getDropdown(id) {
    return document.getElementById(id);
}

export function setDropdownOptions(id, options) {
    const dropdown = getDropdown(id);
    if (dropdown && dropdown.tagName === "AT-DROPDOWN") {
        dropdown.options = options;
    }
}

export function copyToClipboard(elementId, description = "Content", event) {
    const element = document.getElementById(elementId);
    const text = element?.textContent || "";
    // ... rest of function
}
```

### After: `web/src/modules/dom-utils.ts`

```typescript
export function getDropdown(id: string): AtDropdownElement | null {
    const element = document.getElementById(id);
    if (element && element.tagName === "AT-DROPDOWN") {
        return element as AtDropdownElement;
    }
    return null;
}

export function setDropdownOptions(id: string, options: DropdownOption[]): void {
    const dropdown = getDropdown(id);
    if (dropdown) {
        dropdown.options = options;
    }
}

export function copyToClipboard(
    elementId: string,
    description: string = "Content",
    event?: MouseEvent
): void {
    const element = document.getElementById(elementId);
    const text = element?.textContent || "";
    // ... rest of function with proper typing
}
```

### Before: `web/components/ui/at-dropdown.js`

```javascript
export class AtDropdown extends HTMLElement {
  constructor() {
    super();
    this._options = [];
    this._selected = null;
  }

  set options(list) {
    this._options = Array.isArray(list) ? list : [];
    this._render();
  }

  get value() {
    return this._inputEl?.value || '';
  }
}
```

### After: `web/src/components/ui/at-dropdown.ts`

```typescript
export class AtDropdown extends HTMLElement implements AtDropdownElement {
  private _options: DropdownOption[] = [];
  private _selected: DropdownOption | null = null;
  private _inputEl?: HTMLInputElement;
  private _listEl?: HTMLDivElement;
  private _labelEl?: HTMLLabelElement;
  private _onDocumentClick: (event: MouseEvent) => void;
  private _initialized: boolean = false;

  constructor() {
    super();
    this._onDocumentClick = this._handleDocumentClick.bind(this);
  }

  set options(list: DropdownOption[]) {
    this._options = Array.isArray(list) ? list : [];
    this._render();
  }

  get options(): DropdownOption[] {
    return this._options;
  }

  get value(): string {
    return this._inputEl?.value || '';
  }

  set value(val: string) {
    if (this._inputEl) {
      this._inputEl.value = val || '';
    }
  }

  get selectedId(): string | null {
    return this._selected?.id || null;
  }

  get selectedOption(): DropdownOption | null {
    return this._selected;
  }

  private _handleDocumentClick(event: MouseEvent): void {
    if (!this.contains(event.target as Node)) {
      this.close();
    }
  }

  private _select(option: DropdownOption, fireEvent: boolean): void {
    this._selected = option;
    this.value = option.text;
    this.close();

    if (fireEvent) {
      this.dispatchEvent(
        new CustomEvent<DropdownOption>('select', {
          bubbles: true,
          detail: option,
        })
      );
      this.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  // ... rest of methods with proper typing
}

customElements.define('at-dropdown', AtDropdown);
```

## Benefits Analysis

### 1. PyScript Interface Safety

**Before (JavaScript):**
```javascript
// No type checking - errors only at runtime
if (window.compressFormulaFromUI) {
    window.compressFormulaFromUI(tableName, fieldName, depth, format, display);
}
```

**After (TypeScript):**
```typescript
// Compile-time checking of function existence and parameters
if (window.compressFormulaFromUI) {
    window.compressFormulaFromUI(
        tableName,      // type: string
        fieldName,      // type: string
        depth,          // type: number | null
        format,         // type: 'field_ids' | 'field_names'
        display         // type: 'compact' | 'logical'
    );
}
// TypeScript error if wrong parameter types or missing required params
```

### 2. DOM Element Safety

**Before (JavaScript):**
```javascript
const dropdown = document.getElementById("field-dropdown");
dropdown.options = []; // No type checking - runtime error if not at-dropdown
```

**After (TypeScript):**
```typescript
const dropdown = getDropdown("field-dropdown");
if (dropdown) {
    dropdown.options = []; // Type-safe - dropdown is AtDropdownElement
}
// TypeScript error if trying to set invalid properties
```

### 3. AI-Assisted Development

With TypeScript:
- AI can see function signatures and parameter types
- Autocomplete works across the entire codebase
- Refactoring is safer (rename, move, etc.)
- Documentation is embedded in types
- Fewer "undefined is not a function" errors

### 4. Null Safety

**Before (JavaScript):**
```javascript
const element = document.getElementById("my-id");
element.textContent = "Hello"; // Runtime error if element is null
```

**After (TypeScript):**
```typescript
const element = document.getElementById("my-id");
element?.textContent = "Hello"; // Compile-time warning about potential null
// Or with explicit check:
if (element) {
    element.textContent = "Hello"; // Type-safe
}
```

## Build Integration

### Development Workflow

```bash
# Start both watchers in parallel
npm run watch
# or separately:
npm run watch:css  # Tailwind CSS watcher
npm run watch:ts   # TypeScript compiler watcher
```

### Production Build

```bash
npm run build
# Outputs:
# - web/output.css (minified)
# - web/dist/*.js (compiled TypeScript)
```

### GitHub Actions Update

```yaml
- name: Install Node dependencies
  run: npm ci

- name: Build CSS
  run: npm run build:css

- name: Build TypeScript
  run: npm run build:ts

- name: Generate PyScript config
  run: uv run python scripts/generate_pyscript_config.py
```

## Potential Challenges & Solutions

### Challenge 1: Dynamic HTML Script Imports

**Problem:** `index.html` currently uses direct JS imports:
```html
<script type="module" src="./script.js"></script>
```

**Solution:** Update to compiled output:
```html
<script type="module" src="./dist/script.js"></script>
```

### Challenge 2: File Path References in Tailwind

**Problem:** Tailwind scans `web/**/*.{html,js,py}` for classes

**Solution:** Update `tailwind.config.js`:
```javascript
content: [
  "./web/**/*.{html,py}",
  "./web/src/**/*.ts",  // TypeScript source
  "./web/dist/**/*.js", // Compiled output (if needed)
]
```

### Challenge 3: Source Maps in Browser

**Problem:** Debugging shows compiled JS, not original TS

**Solution:** Enable source maps in `tsconfig.json`:
```json
{
  "sourceMap": true,
  "declarationMap": true
}
```

### Challenge 4: PyScript Type Definitions Incomplete

**Problem:** Python functions may change without updating TS types

**Solution:** 
1. Document Python→JS interface in code comments
2. Add runtime checks for critical functions
3. Create shared constants file between Python and TS

## Testing Strategy

### 1. Incremental Testing
- Test each converted module in isolation
- Verify build output matches expected behavior
- Check that existing functionality still works

### 2. Type Coverage
```bash
# Check type coverage (install separately)
npm install --save-dev type-coverage
npx type-coverage
```

**Goal:** >90% type coverage

### 3. Browser Testing
- Test in Chrome/Firefox/Safari
- Verify PyScript integration still works
- Check that all tabs function correctly
- Test dark mode toggle
- Verify dropdowns work as expected

## Documentation Updates Required

1. **README.md**: Update development setup instructions
2. **.github/copilot-instructions.md**: Add TypeScript conventions
3. **web/README.md** (new): TypeScript architecture guide
4. **package.json**: Document new scripts

## Rollback Plan

If issues arise:
1. Keep original JS files until migration is complete and tested
2. Git branch strategy: `feature/typescript-migration`
3. Can always revert to `main` branch
4. Compiled JS in `dist/` is functionally equivalent to original JS

## Timeline Estimate

- **Setup (Day 1):** 2-3 hours
- **Utilities (Day 1-2):** 3-4 hours
- **Web Components (Day 2-3):** 4-6 hours
- **Tab Modules (Day 3-4):** 6-8 hours
- **Main Script (Day 4):** 2-3 hours
- **Integration & Testing (Day 5):** 4-6 hours

**Total:** 21-30 hours (roughly 1 week of focused work)

## Success Criteria

✅ All JavaScript files converted to TypeScript  
✅ `npm run build` completes without errors  
✅ Type coverage >90%  
✅ All tabs functional in browser  
✅ PyScript integration working  
✅ Dark mode toggle working  
✅ No console errors in browser  
✅ CI/CD pipeline updated and passing  
✅ Documentation updated  

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Create feature branch:** `git checkout -b feature/typescript-migration`
3. **Start Phase 1:** Install dependencies and create config files
4. **Test build pipeline:** Ensure TS compiles before converting files
5. **Begin Phase 2:** Convert utility modules first

## Conclusion

Migrating to TypeScript is a **worthwhile investment** that will:
- Improve code quality and maintainability
- Make AI-assisted development more reliable
- Catch bugs at compile time
- Provide better IDE support
- Establish a professional foundation for future features

The migration is **low-risk** because:
- We already have an npm build pipeline
- TypeScript compiles to JavaScript (same output)
- Can be done incrementally (module by module)
- Easy to rollback if needed

The **biggest win** is typing the PyScript/JavaScript interface, which will prevent runtime errors and make the codebase much more robust for both human and AI developers.
