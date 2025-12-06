/**
 * Session types
 */

export interface SessionResponse {
  expiresAt: string;
  userId?: string;
  tenantId?: string | null;
  scopes?: string[];
  profile?: unknown;
}
