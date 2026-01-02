import type { AirtableMetadata, AirtableTable, SchemaPayload } from '../../types/pyscript';

const STORAGE_KEY = 'airtableSchema';
const VERSION_KEY = 'airtableSchemaVersion';
const CURRENT_VERSION = 1;

/**
 * Save Airtable schema to localStorage
 * @param schema - The Airtable metadata to save
 */
export function saveSchema(schema: AirtableMetadata): void {
  if (!schema) return;
  
  const payload: SchemaPayload = {
    version: CURRENT_VERSION,
    timestamp: new Date().toISOString(),
    schema,
  };
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  localStorage.setItem(VERSION_KEY, String(CURRENT_VERSION));
}

/**
 * Retrieve Airtable schema from localStorage
 * @returns The stored schema payload or null if not found
 */
export function getSchema(): SchemaPayload | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  
  try {
    const parsed = JSON.parse(raw) as SchemaPayload;
    if (!parsed.schema) return null;
    
    // Future upgrade: migrate older versions here
    return parsed;
  } catch (error) {
    console.warn('Failed to parse schema from storage', error);
    return null;
  }
}

/**
 * Clear Airtable schema from localStorage
 */
export function clearSchema(): void {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(VERSION_KEY);
}

/**
 * Get all tables from the stored schema
 * @returns Array of tables or empty array if no schema exists
 */
export function getTables(): AirtableTable[] {
  const payload = getSchema();
  return payload?.schema?.tables || [];
}

/**
 * Cache a graph/diagram in localStorage
 * @param key - The storage key for the cached graph
 * @param value - The graph data as a string
 */
export function setCachedGraph(key: string, value: string): void {
  localStorage.setItem(key, value);
}

/**
 * Retrieve a cached graph/diagram from localStorage
 * @param key - The storage key for the cached graph
 * @returns The cached graph data or null if not found
 */
export function getCachedGraph(key: string): string | null {
  return localStorage.getItem(key);
}
