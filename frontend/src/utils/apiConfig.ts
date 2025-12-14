/**
 * Shared API configuration helper.
 * Ensures we always point to the same /api base without double-prefixing.
 */
const rawApi = (import.meta.env.VITE_API_URL || 'http://localhost:5000/api').trim();
const normalized = rawApi.replace(/\/$/, '');

export const API_BASE_URL = normalized.endsWith('/api')
  ? normalized
  : `${normalized}/api`;
