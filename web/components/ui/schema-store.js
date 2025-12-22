const STORAGE_KEY = 'airtableSchema';
const VERSION_KEY = 'airtableSchemaVersion';
const CURRENT_VERSION = 1;

export function saveSchema(schema) {
  if (!schema) return;
  const payload = {
    version: CURRENT_VERSION,
    timestamp: new Date().toISOString(),
    schema,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  localStorage.setItem(VERSION_KEY, String(CURRENT_VERSION));
}

export function getSchema() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed.schema) return null;
    // Future upgrade: migrate older versions here
    return parsed;
  } catch (error) {
    console.warn('Failed to parse schema from storage', error);
    return null;
  }
}

export function clearSchema() {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem(VERSION_KEY);
}

export function getTables() {
  const payload = getSchema();
  return payload?.schema?.tables || [];
}

export function setCachedGraph(key, value) {
  localStorage.setItem(key, value);
}

export function getCachedGraph(key) {
  return localStorage.getItem(key);
}
