export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
export const USE_API_MOCK = process.env.AGENT_API_MOCK === 'true';
export const ACCESS_TOKEN_COOKIE = 'aa_access_token';
export const REFRESH_TOKEN_COOKIE = 'aa_refresh_token';
export const SESSION_META_COOKIE = 'aa_session_meta';
