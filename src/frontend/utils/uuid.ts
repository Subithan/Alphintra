/**
 * UUID utility functions for generating and validating UUIDs
 */

/**
 * Generate a random UUID v4
 */
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Validate if a string is a valid UUID format
 */
export function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
}

/**
 * Convert a non-UUID string to a deterministic UUID (for development/testing)
 */
export function stringToUUID(str: string): string {
  if (isValidUUID(str)) {
    return str;
  }
  
  // Create a simple hash of the string and format as UUID
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  
  // Convert hash to hex and pad to create UUID-like string
  const hex = Math.abs(hash).toString(16).padStart(8, '0');
  return `${hex.slice(0,8)}-${hex.slice(0,4)}-4${hex.slice(0,3)}-8${hex.slice(0,3)}-${hex}${hex.slice(0,4)}`;
}