/**
 * Type definitions for PyScript global functions exposed from Python
 * 
 * These functions are exported from Python modules to the JavaScript window object
 * via the pattern: window.functionName = my_python_function
 */

// Airtable metadata types
export interface AirtableField {
  id: string;
  name: string;
  type: string;
  options?: {
    formula?: string;
    referencedFieldIds?: string[];
    inverseLinkFieldId?: string;
    linkedTableId?: string;
    [key: string]: any;
  };
}

export interface AirtableTable {
  id: string;
  name: string;
  fields: AirtableField[];
  primaryFieldId?: string;
  description?: string;
}

export interface AirtableMetadata {
  tables: AirtableTable[];
}

export interface SchemaPayload {
  version: number;
  timestamp: string;
  schema: AirtableMetadata;
}

// Dropdown option structure used across the app
export interface DropdownOption {
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
    // Dependency Mapper Tab (web/tabs/dependency_mapper.py)
    parametersChanged(): void;
    updateMermaidGraph(tableId: string, fieldId: string, flowchartType: string): void;
    
    // Formula Compressor Tab (web/tabs/formula_compressor.py)
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
    
    // Formula Evaluator Tab (web/tabs/formula_evaluator.py)
    loadFieldDependencies(): void;
    evaluateFormulaWithValues(
      fieldId: string,
      dependencies: Record<string, any>,
      outputFormat: 'field_ids' | 'field_names'
    ): void;
    
    // Complexity Scorecard Tab (web/tabs/complexity_scorecard.py)
    generateComplexityScorecard?(): void;
    getComplexityScorecardData?(filterTable?: string | null, minScore?: number): any;
    exportComplexityCSV?(): string;
    getComplexitySummary?(): any;
    
    // Unused Fields Tab (web/tabs/unused_fields.py)
    generateUnusedFieldsReport?(): void;
    getFieldTypesForDropdown?(): any[];
    getUnusedFieldsData?(filterTable?: string, fieldType?: string): any;
    exportUnusedFieldsCSV?(filterTable?: string, fieldType?: string): string;
    getUnusedFieldsSummary?(filterTable?: string, fieldType?: string): any;
    
    // Table Analysis Tab (web/tabs/table_analysis.py)
    generateTableDependencies?(): void;
    getTableDependencies?(): any;
    
    // Formula Grapher Tab (web/tabs/formula_grapher.py)
    generateFormulaGraph?(tableName: string, fieldName: string): void;
    getFormulaForDisplay?(tableName: string, fieldName: string): string;
    graphFormulaFromUI?(tableName: string, fieldName: string, expandFields?: boolean, maxDepth?: number | null, direction?: string): void;
  }
}
