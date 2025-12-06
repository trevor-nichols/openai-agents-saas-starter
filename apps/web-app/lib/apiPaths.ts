/**
 * Centralizes the base prefix for versioned BFF routes to avoid drift when paths change.
 */
export const API_V1_BASE = '/api/v1';

export const apiV1Path = (suffix: string) => `${API_V1_BASE}${suffix.startsWith('/') ? suffix : `/${suffix}`}`;
