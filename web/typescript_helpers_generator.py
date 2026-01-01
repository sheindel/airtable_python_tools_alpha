"""
TypeScript Helpers Generator - Generate helper functions and utilities for Airtable records

This module generates TypeScript helper functions that provide type-safe access to Airtable records,
including getField/setField functions, field ID lookups, and record manipulation utilities.
"""

from typing import Dict, Any, List
import sys
sys.path.append("web")

from types_generator import _sanitize_name


def generate_typescript_helpers(metadata: Dict[str, Any]) -> str:
    """
    Generate TypeScript helper functions for type-safe record access
    
    Args:
        metadata: Airtable metadata dictionary
    
    Returns:
        TypeScript code as a string with helper functions
    """
    tables = metadata.get("tables", [])
    table_names = [table.get("name", "") for table in tables]
    
    lines = [
        "// @ts-nocheck",
        "// Generated TypeScript helpers for Airtable records",
        "",
        "import { FieldSet, Record as AirtableRecord } from 'airtable'",
        "import * as Types from './types'",
        "",
        "// Re-export all types for convenience",
        "export * from './types'",
        "",
        "// ============================================================================",
        "// Core Type Definitions",
        "// ============================================================================",
        "",
        "export type ATRecord<T extends FieldSet> = T & {",
        "  id: string",
        "  _table?: string",
        "  _rawFields?: Record<string, any>",
        "}",
        "",
        "export type TableName = " + " | ".join([f"'{name}'" for name in table_names]),
        "",
        "export type TableTypes = {",
    ]
    
    for table in tables:
        table_name = table.get("name", "")
        lines.append(f"  '{table_name}': Types.{table_name}")
    
    lines.extend([
        "}",
        "",
        "// ============================================================================",
        "// Field ID Mapping Types",
        "// ============================================================================",
        "",
        "export type FieldIdMappings = {",
    ])
    
    for table in tables:
        table_name = table.get("name", "")
        lines.append(f"  '{table_name}': typeof Types.{table_name}FieldIdMapping")
    
    lines.extend([
        "}",
        "",
        "// ============================================================================",
        "// Helper Functions",
        "// ============================================================================",
        "",
        "/**",
        " * Get a field ID from a table and field name",
        " * @param tableName - The name of the table",
        " * @param fieldName - The name of the field",
        " * @returns The field ID",
        " */",
        "export function getFieldId<T extends TableName>(",
        "  tableName: T,",
        "  fieldName: keyof TableTypes[T]",
        "): string {",
        "  const mappings: Record<TableName, Record<string, string>> = {",
    ])
    
    for table in tables:
        table_name = table.get("name", "")
        lines.append(f"    '{table_name}': Types.{table_name}FieldIdMapping,")
    
    lines.extend([
        "  }",
        "  return mappings[tableName][fieldName as string] || fieldName as string",
        "}",
        "",
        "/**",
        " * Get multiple field IDs from a table",
        " * @param tableName - The name of the table",
        " * @param fieldNames - Array of field names",
        " * @returns Array of field IDs",
        " */",
        "export function getFieldIds<T extends TableName>(",
        "  tableName: T,",
        "  fieldNames: readonly (keyof TableTypes[T])[]",
        "): string[] {",
        "  return fieldNames.map(fieldName => getFieldId(tableName, fieldName))",
        "}",
        "",
        "/**",
        " * Get a field value from a record with proper typing",
        " * @param record - The Airtable record",
        " * @param fieldName - The name of the field (or field ID if useFieldId is true)",
        " * @param defaultValue - Default value if field is undefined",
        " * @param useFieldId - Whether fieldName is actually a field ID",
        " * @returns The field value with proper typing",
        " */",
        "export function getField<",
        "  T extends FieldSet,",
        "  K extends keyof T",
        ">(",
        "  record: ATRecord<Partial<T>> | undefined,",
        "  fieldName: K,",
        "  defaultValue?: T[K],",
        "  useFieldId: boolean = false",
        "): T[K] | undefined {",
        "  if (!record) return defaultValue",
        "  ",
        "  const key = useFieldId ? fieldName : fieldName",
        "  const value = record[key as keyof typeof record]",
        "  ",
        "  return value !== undefined ? value as T[K] : defaultValue",
        "}",
        "",
        "/**",
        " * Set a field value on a record with proper typing",
        " * @param record - The Airtable record",
        " * @param fieldName - The name of the field (or field ID if useFieldId is true)",
        " * @param value - The value to set",
        " * @param useFieldId - Whether fieldName is actually a field ID",
        " */",
        "export function setField<",
        "  T extends FieldSet,",
        "  K extends keyof T",
        ">(",
        "  record: ATRecord<Partial<T>>,",
        "  fieldName: K,",
        "  value: T[K],",
        "  useFieldId: boolean = false",
        "): void {",
        "  const key = useFieldId ? fieldName : fieldName",
        "  ;(record as any)[key] = value",
        "}",
        "",
        "/**",
        " * Get multiple field values from a record",
        " * @param record - The Airtable record",
        " * @param fieldNames - Array of field names",
        " * @returns Object with field names as keys and their values",
        " */",
        "export function getFields<",
        "  T extends FieldSet,",
        "  K extends keyof T",
        ">(",
        "  record: ATRecord<Partial<T>> | undefined,",
        "  fieldNames: readonly K[]",
        "): Partial<Pick<T, K>> {",
        "  if (!record) return {}",
        "  ",
        "  const result: Partial<Pick<T, K>> = {}",
        "  for (const fieldName of fieldNames) {",
        "    const value = getField(record, fieldName)",
        "    if (value !== undefined) {",
        "      result[fieldName] = value",
        "    }",
        "  }",
        "  return result",
        "}",
        "",
        "/**",
        " * Check if a record has a specific field with a non-null/undefined value",
        " * @param record - The Airtable record",
        " * @param fieldName - The name of the field",
        " * @returns True if field exists and has a value",
        " */",
        "export function hasField<",
        "  T extends FieldSet,",
        "  K extends keyof T",
        ">(",
        "  record: ATRecord<Partial<T>> | undefined,",
        "  fieldName: K",
        "): boolean {",
        "  if (!record) return false",
        "  const value = record[fieldName as keyof typeof record]",
        "  return value !== undefined && value !== null",
        "}",
        "",
        "/**",
        " * Create a partial record update object with proper typing",
        " * @param id - The record ID",
        " * @param fields - The fields to update",
        " * @returns A record update object",
        " */",
        "export function createUpdate<T extends FieldSet>(",
        "  id: string,",
        "  fields: Partial<T>",
        "): ATRecord<Partial<T>> {",
        "  return { id, ...fields } as ATRecord<Partial<T>>",
        "}",
        "",
        "/**",
        " * Type guard to check if a value is a valid Airtable record",
        " * @param value - The value to check",
        " * @returns True if value is a record with an ID",
        " */",
        "export function isRecord<T extends FieldSet>(",
        "  value: any",
        "): value is ATRecord<T> {",
        "  return (",
        "    typeof value === 'object' &&",
        "    value !== null &&",
        "    'id' in value &&",
        "    typeof value.id === 'string'",
        "  )",
        "}",
        "",
        "/**",
        " * Convert an Airtable SDK record to our ATRecord format",
        " * @param record - The Airtable SDK record",
        " * @returns ATRecord with proper typing",
        " */",
        "export function fromAirtableRecord<T extends FieldSet>(",
        "  record: AirtableRecord<T>",
        "): ATRecord<T> {",
        "  return {",
        "    id: record.id,",
        "    ...record.fields,",
        "    _table: record._table?.name,",
        "    _rawFields: record.fields",
        "  } as ATRecord<T>",
        "}",
        "",
        "/**",
        " * Convert multiple Airtable SDK records to ATRecord format",
        " * @param records - Array of Airtable SDK records",
        " * @returns Array of ATRecords",
        " */",
        "export function fromAirtableRecords<T extends FieldSet>(",
        "  records: AirtableRecord<T>[]",
        "): ATRecord<T>[] {",
        "  return records.map(fromAirtableRecord)",
        "}",
        "",
        "/**",
        " * Extract only the fields from a record (without id and metadata)",
        " * @param record - The ATRecord",
        " * @returns Just the fields object",
        " */",
        "export function extractFields<T extends FieldSet>(",
        "  record: ATRecord<T>",
        "): T {",
        "  const { id, _table, _rawFields, ...fields } = record",
        "  return fields as T",
        "}",
    ])
    
    return "\n".join(lines)


def generate_typescript_helpers_js(metadata: Dict[str, Any]) -> str:
    """
    Generate JavaScript implementation file for TypeScript helpers
    
    Args:
        metadata: Airtable metadata dictionary
    
    Returns:
        JavaScript code as a string
    """
    tables = metadata.get("tables", [])
    
    lines = [
        "// Generated JavaScript helpers for Airtable records",
        "// This is the runtime implementation of the TypeScript helpers",
        "",
        "import * as Types from './types.js'",
        "",
        "// ============================================================================",
        "// Field ID Mapping",
        "// ============================================================================",
        "",
        "const FIELD_ID_MAPPINGS = {",
    ]
    
    for table in tables:
        table_name = table.get("name", "")
        lines.append(f"  '{table_name}': Types.{table_name}FieldIdMapping,")
    
    lines.extend([
        "}",
        "",
        "// ============================================================================",
        "// Helper Functions",
        "// ============================================================================",
        "",
        "export function getFieldId(tableName, fieldName) {",
        "  const mapping = FIELD_ID_MAPPINGS[tableName]",
        "  return mapping?.[fieldName] || fieldName",
        "}",
        "",
        "export function getFieldIds(tableName, fieldNames) {",
        "  return fieldNames.map(fieldName => getFieldId(tableName, fieldName))",
        "}",
        "",
        "export function getField(record, fieldName, defaultValue = undefined, useFieldId = false) {",
        "  if (!record) return defaultValue",
        "  const key = useFieldId ? fieldName : fieldName",
        "  const value = record[key]",
        "  return value !== undefined ? value : defaultValue",
        "}",
        "",
        "export function setField(record, fieldName, value, useFieldId = false) {",
        "  if (!record) return",
        "  const key = useFieldId ? fieldName : fieldName",
        "  record[key] = value",
        "}",
        "",
        "export function getFields(record, fieldNames) {",
        "  if (!record) return {}",
        "  const result = {}",
        "  for (const fieldName of fieldNames) {",
        "    const value = getField(record, fieldName)",
        "    if (value !== undefined) {",
        "      result[fieldName] = value",
        "    }",
        "  }",
        "  return result",
        "}",
        "",
        "export function hasField(record, fieldName) {",
        "  if (!record) return false",
        "  const value = record[fieldName]",
        "  return value !== undefined && value !== null",
        "}",
        "",
        "export function createUpdate(id, fields) {",
        "  return { id, ...fields }",
        "}",
        "",
        "export function isRecord(value) {",
        "  return (",
        "    typeof value === 'object' &&",
        "    value !== null &&",
        "    'id' in value &&",
        "    typeof value.id === 'string'",
        "  )",
        "}",
        "",
        "export function fromAirtableRecord(record) {",
        "  return {",
        "    id: record.id,",
        "    ...record.fields,",
        "    _table: record._table?.name,",
        "    _rawFields: record.fields",
        "  }",
        "}",
        "",
        "export function fromAirtableRecords(records) {",
        "  return records.map(fromAirtableRecord)",
        "}",
        "",
        "export function extractFields(record) {",
        "  const { id, _table, _rawFields, ...fields } = record",
        "  return fields",
        "}",
    ])
    
    return "\n".join(lines)


def generate_typescript_examples(metadata: Dict[str, Any]) -> str:
    """
    Generate TypeScript usage examples for the generated types and helpers
    
    Args:
        metadata: Airtable metadata dictionary
    
    Returns:
        TypeScript example code as a string
    """
    tables = metadata.get("tables", [])
    
    # Pick first table for examples
    example_table = tables[0] if tables else None
    if not example_table:
        return "// No tables found in metadata"
    
    table_name = example_table.get("name", "")
    fields = example_table.get("fields", [])
    
    # Get a few example fields
    text_field = next((f for f in fields if f.get("type") in ["singleLineText", "multilineText"]), None)
    number_field = next((f for f in fields if f.get("type") == "number"), None)
    checkbox_field = next((f for f in fields if f.get("type") == "checkbox"), None)
    
    lines = [
        "// @ts-nocheck",
        "// Usage Examples for Generated Airtable Types and Helpers",
        "// This file demonstrates how to use the generated types and helper functions",
        "",
        "import Airtable from 'airtable'",
        "import { ",
        "  ATRecord,",
        f"  {table_name},",
        "  getField,",
        "  setField,",
        "  getFieldId,",
        "  getFieldIds,",
        "  hasField,",
        "  createUpdate,",
        "  fromAirtableRecord,",
        "  fromAirtableRecords,",
        "  extractFields",
        "} from './helpers'",
        "",
        "// ============================================================================",
        "// Example 1: Initialize Airtable Connection",
        "// ============================================================================",
        "",
        "const base = new Airtable({ apiKey: 'YOUR_API_KEY' }).base('YOUR_BASE_ID')",
        "",
        "// ============================================================================",
        "// Example 2: Fetch Records with Proper Typing",
        "// ============================================================================",
        "",
        f"async function fetchRecords() {{",
        f"  const records = await base('{table_name}').select({{",
        "    maxRecords: 10,",
        "    view: 'Grid view'",
        "  }).all()",
        "",
        "  // Convert Airtable records to typed records",
        f"  const typedRecords: ATRecord<{table_name}>[] = fromAirtableRecords(records)",
        "",
        "  return typedRecords",
        "}",
        "",
        "// ============================================================================",
        "// Example 3: Access Fields Safely",
        "// ============================================================================",
        "",
        f"async function accessFields() {{",
        f"  const records = await fetchRecords()",
        "  const record = records[0]",
        "",
    ]
    
    if text_field:
        field_name = text_field.get("name", "")
        lines.extend([
            f"  // Access field with proper typing",
            f"  const value = getField(record, '{field_name}')",
            f"  console.log('Field value:', value)",
            "",
        ])
    
    if checkbox_field:
        field_name = checkbox_field.get("name", "")
        lines.extend([
            f"  // Check if field exists and has value",
            f"  if (hasField(record, '{field_name}')) {{",
            f"    console.log('{field_name} is checked')",
            "  }",
            "",
        ])
    
    lines.extend([
        "}",
        "",
        "// ============================================================================",
        "// Example 4: Get Field IDs",
        "// ============================================================================",
        "",
        "function workWithFieldIds() {",
        f"  // Get field ID for a specific field",
    ])
    
    if text_field:
        field_name = text_field.get("name", "")
        lines.extend([
            f"  const fieldId = getFieldId('{table_name}', '{field_name}')",
            f"  console.log('Field ID:', fieldId)",
            "",
        ])
    
    lines.extend([
        f"  // Get multiple field IDs at once",
    ])
    
    field_names = [f.get("name", "") for f in fields[:3]]
    if field_names:
        field_names_str = "', '".join(field_names)
        lines.extend([
            f"  const fieldIds = getFieldIds('{table_name}', ['{field_names_str}'])",
            "  console.log('Field IDs:', fieldIds)",
        ])
    
    lines.extend([
        "}",
        "",
        "// ============================================================================",
        "// Example 5: Update Records",
        "// ============================================================================",
        "",
        f"async function updateRecords() {{",
        f"  const records = await fetchRecords()",
        "  const record = records[0]",
        "",
    ])
    
    if text_field and number_field:
        text_name = text_field.get("name", "")
        number_name = number_field.get("name", "")
        lines.extend([
            f"  // Modify field values",
            f"  setField(record, '{text_name}', 'Updated value')",
            f"  setField(record, '{number_name}', 42)",
            "",
            f"  // Create update object for Airtable API",
            "  const update = createUpdate(record.id, extractFields(record))",
            "",
            f"  // Send update to Airtable",
            f"  await base('{table_name}').update([update])",
            "",
        ])
    
    lines.extend([
        "}",
        "",
        "// ============================================================================",
        "// Example 6: Create New Records",
        "// ============================================================================",
        "",
        f"async function createRecords() {{",
        f"  const newRecord: Partial<{table_name}> = {{",
    ])
    
    if text_field:
        field_name = text_field.get("name", "")
        lines.append(f"    '{field_name}': 'New record value',")
    
    if number_field:
        field_name = number_field.get("name", "")
        lines.append(f"    '{field_name}': 100,")
    
    if checkbox_field:
        field_name = checkbox_field.get("name", "")
        lines.append(f"    '{field_name}': true,")
    
    lines.extend([
        "  }",
        "",
        f"  const createdRecords = await base('{table_name}').create([",
        "    { fields: newRecord }",
        "  ])",
        "",
        "  return fromAirtableRecords(createdRecords)",
        "}",
        "",
        "// ============================================================================",
        "// Example 7: Filter and Query Records",
        "// ============================================================================",
        "",
        f"async function queryRecords() {{",
    ])
    
    if text_field:
        field_name = text_field.get("name", "")
        field_id = text_field.get("id", "")
        lines.extend([
            f"  // Use field IDs in formulas for more reliable queries",
            f"  const fieldId = getFieldId('{table_name}', '{field_name}')",
            f"  ",
            f"  const records = await base('{table_name}').select({{",
            "    filterByFormula: `{${fieldId}} != ''`,",
            "    sort: [{ field: fieldId, direction: 'asc' }]",
            "  }).all()",
            "",
            "  return fromAirtableRecords(records)",
        ])
    
    lines.extend([
        "}",
        "",
        "// ============================================================================",
        "// Example 8: Batch Operations",
        "// ============================================================================",
        "",
        f"async function batchUpdate() {{",
        f"  const records = await fetchRecords()",
        "",
    ])
    
    if text_field:
        field_name = text_field.get("name", "")
        lines.extend([
            f"  // Prepare batch updates",
            "  const updates = records.map(record => {",
            f"    setField(record, '{field_name}', `Updated: ${{record.id}}`)",
            "    return createUpdate(record.id, extractFields(record))",
            "  })",
            "",
            f"  // Send batch update to Airtable (max 10 at a time)",
            f"  const batchSize = 10",
            f"  for (let i = 0; i < updates.length; i += batchSize) {{",
            f"    const batch = updates.slice(i, i + batchSize)",
            f"    await base('{table_name}').update(batch)",
            "  }",
        ])
    
    lines.extend([
        "}",
        "",
        "// ============================================================================",
        "// Example 9: Type-Safe Field Access with Direct Record Access",
        "// ============================================================================",
        "",
        f"async function directFieldAccess() {{",
        f"  const records = await fetchRecords()",
        "  const record = records[0]",
        "",
    ])
    
    if text_field:
        field_name = text_field.get("name", "")
        lines.extend([
            f"  // Direct access with TypeScript autocomplete",
            f"  const value = record['{field_name}']",
            f"  console.log('Direct field access:', value)",
            "",
        ])
    
    lines.extend([
        "  // Extract only fields (without id and metadata)",
        "  const fields = extractFields(record)",
        "  console.log('Fields only:', fields)",
        "}",
        "",
        "// ============================================================================",
        "// Running Examples",
        "// ============================================================================",
        "",
        "async function main() {",
        "  try {",
        "    console.log('Fetching records...')",
        "    await accessFields()",
        "    ",
        "    console.log('Working with field IDs...')",
        "    workWithFieldIds()",
        "    ",
        "    console.log('Examples completed successfully!')",
        "  } catch (error) {",
        "    console.error('Error running examples:', error)",
        "  }",
        "}",
        "",
        "// Uncomment to run examples",
        "// main()",
    ])
    
    return "\n".join(lines)
