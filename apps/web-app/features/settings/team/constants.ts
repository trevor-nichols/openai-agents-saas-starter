import type { TeamRole } from '@/types/team';

export const TEAM_SETTINGS_COPY = {
  header: {
    eyebrow: 'Settings',
    title: 'Team management',
    description: 'Manage tenant members, assign roles, and control invite access in one place.',
  },
  emptyMembers: {
    title: 'No team members yet',
    description: 'Invite teammates or add an existing user to get started.',
  },
  emptyInvites: {
    title: 'No invites sent',
    description: 'Issue an invite to onboard a teammate.',
  },
} as const;

export const TEAM_ROLE_LABELS: Record<TeamRole, string> = {
  viewer: 'Viewer',
  member: 'Member',
  admin: 'Admin',
  owner: 'Owner',
};

export const TEAM_ROLE_HELPERS: Record<TeamRole, string> = {
  viewer: 'Read-only access to conversations and tools.',
  member: 'Can collaborate on conversations and tools.',
  admin: 'Full workspace access plus billing and operations.',
  owner: 'Highest privilege, including owner role management.',
};
