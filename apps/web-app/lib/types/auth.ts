export interface UserSessionTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_at: string;
  refresh_expires_at: string;
  kid: string;
  refresh_kid: string;
  scopes: string[];
  tenant_id: string;
  user_id: string;
}

export interface SessionSummary {
  userId: string;
  tenantId: string;
  scopes: string[];
  expiresAt: string;
}
