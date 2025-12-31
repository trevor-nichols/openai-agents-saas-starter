const ADMIN_ROLES = new Set(['admin', 'owner']);
const ADMIN_SCOPES = new Set(['billing:manage', 'support:read', 'activity:read']);
const OPERATOR_SCOPES = new Set(['support:*', 'platform:operator']);

export function isTenantAdminRole(role?: string | null): boolean {
  if (!role) {
    return false;
  }
  return ADMIN_ROLES.has(role.toLowerCase());
}

export function isTenantAdmin({
  role,
  scopes,
}: {
  role?: string | null;
  scopes?: string[] | null;
}): boolean {
  if (isTenantAdminRole(role)) {
    return true;
  }
  if (!scopes || scopes.length === 0) {
    return false;
  }
  return scopes.some((scope) => ADMIN_SCOPES.has(scope));
}

export function hasOperatorScope(scopes?: string[] | null): boolean {
  if (!scopes || scopes.length === 0) {
    return false;
  }
  return scopes.some((scope) => OPERATOR_SCOPES.has(scope));
}

export const TENANT_ADMIN_ROLES = Array.from(ADMIN_ROLES);
