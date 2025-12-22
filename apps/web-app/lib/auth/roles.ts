const ADMIN_ROLES = new Set(['admin', 'owner']);
const ADMIN_SCOPES = new Set(['billing:manage', 'support:read', 'activity:read']);

export function isTenantAdmin({
  role,
  scopes,
}: {
  role?: string | null;
  scopes?: string[] | null;
}): boolean {
  if (role && ADMIN_ROLES.has(role.toLowerCase())) {
    return true;
  }
  if (!scopes || scopes.length === 0) {
    return false;
  }
  return scopes.some((scope) => ADMIN_SCOPES.has(scope));
}

export const TENANT_ADMIN_ROLES = Array.from(ADMIN_ROLES);
