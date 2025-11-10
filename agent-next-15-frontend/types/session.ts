/**
 * Session types
 */

export interface SessionResponse {
  expiresAt: string;
  userId?: string;
  tenantId?: string;
}
