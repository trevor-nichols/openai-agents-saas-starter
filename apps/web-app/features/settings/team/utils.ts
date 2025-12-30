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

export function resolveRoleLabel(role: TeamRole): string {
  return TEAM_ROLE_LABELS[role] ?? formatStatus(role);
}

export function normalizeOptionalString(value: unknown): unknown {
  if (typeof value !== 'string') {
    return value;
  }
  const trimmed = value.trim();
  return trimmed.length === 0 ? undefined : trimmed;
}

export function getAssignableRoles(actorRole: TeamRole | null): TeamRole[] {
  if (!actorRole) return [];
  if (actorRole === 'owner') {
    return [...TEAM_ROLE_ORDER];
  }
  if (actorRole === 'admin') {
    return TEAM_ROLE_ORDER.filter((role) => role !== 'owner');
  }
  return [];
}

export function canEditMemberRole(
  actorRole: TeamRole | null,
  targetRole: TeamRole,
  ownerCount?: number,
): boolean {
  if (!actorRole) return false;

  if (targetRole === 'owner') {
    if (typeof ownerCount !== 'number' || ownerCount <= 1) {
      return false;
    }
  }
  if (actorRole === 'owner') return true;
  if (actorRole === 'admin') return targetRole !== 'owner';
  return false;
}

export function canRemoveMember(
  actorRole: TeamRole | null,
  targetRole: TeamRole,
  ownerCount?: number,
): boolean {
  if (!actorRole) return false;
  if (actorRole === 'owner') {
    if (targetRole === 'owner') {
      if (typeof ownerCount !== 'number' || ownerCount <= 1) {
        return false;
      }
    }
    return true;
  }
  if (actorRole === 'admin') {
    return targetRole !== 'owner';
  }
  return false;
}
