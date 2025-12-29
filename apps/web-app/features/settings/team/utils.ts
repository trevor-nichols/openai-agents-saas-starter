import type { TeamRole } from '@/types/team';
import { TEAM_ROLE_ORDER } from '@/types/team';
import { TEAM_ROLE_LABELS } from './constants';

export function formatDateTime(value: string | null): string {
  if (!value) return '—';
  try {
    const formatter = new Intl.DateTimeFormat('en-US', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
    return formatter.format(new Date(value));
  } catch {
    return value;
  }
}

export function formatStatus(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (match) => match.toUpperCase());
}

export function resolveRoleLabel(role: string): string {
  return TEAM_ROLE_LABELS[role as TeamRole] ?? formatStatus(role);
}

export function normalizeOptionalString(value: unknown): unknown {
  if (typeof value !== 'string') {
    return value;
  }
  const trimmed = value.trim();
  return trimmed.length === 0 ? undefined : trimmed;
}

export function getAssignableRoles(actorRole: string | null): TeamRole[] {
  if (!actorRole) return [];
  const normalized = actorRole.toLowerCase();
  if (normalized === 'owner') {
    return [...TEAM_ROLE_ORDER];
  }
  if (normalized === 'admin') {
    return TEAM_ROLE_ORDER.filter((role) => role !== 'owner');
  }
  return [];
}

export function canEditMemberRole(
  actorRole: string | null,
  targetRole: string,
  ownerCount?: number,
): boolean {
  if (!actorRole) return false;
  const normalizedActor = actorRole.toLowerCase();
  const normalizedTarget = targetRole.toLowerCase();

  if (normalizedTarget === 'owner' && typeof ownerCount === 'number' && ownerCount <= 1) {
    return false;
  }
  if (normalizedActor === 'owner') return true;
  if (normalizedActor === 'admin') return normalizedTarget !== 'owner';
  return false;
}

export function canRemoveMember(
  actorRole: string | null,
  targetRole: string,
  ownerCount: number,
): boolean {
  if (!actorRole) return false;
  const normalizedActor = actorRole.toLowerCase();
  const normalizedTarget = targetRole.toLowerCase();
  if (normalizedActor === 'owner') {
    if (normalizedTarget === 'owner' && ownerCount <= 1) {
      return false;
    }
    return true;
  }
  if (normalizedActor === 'admin') {
    return normalizedTarget !== 'owner';
  }
  return false;
}
