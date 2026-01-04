import 'server-only';
import { API_BASE_URL } from '@/lib/config/server';

const normalizedBaseUrl = API_BASE_URL.endsWith('/')
  ? API_BASE_URL.slice(0, -1)
  : API_BASE_URL;

export function getApiBaseUrl(): string {
  return normalizedBaseUrl;
}
