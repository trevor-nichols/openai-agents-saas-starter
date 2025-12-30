import { describe, expect, it } from 'vitest';

import { canEditMemberRole, canRemoveMember, getAssignableRoles } from '../utils';

describe('team settings utils', () => {
  it('returns assignable roles for owners and admins', () => {
    expect(getAssignableRoles('owner')).toEqual(['viewer', 'member', 'admin', 'owner']);
    expect(getAssignableRoles('admin')).toEqual(['viewer', 'member', 'admin']);
    expect(getAssignableRoles('member')).toEqual([]);
  });

  it('enforces owner-only edits for owner roles', () => {
    expect(canEditMemberRole('owner', 'owner', 2)).toBe(true);
    expect(canEditMemberRole('owner', 'owner', 1)).toBe(false);
    expect(canEditMemberRole('owner', 'owner')).toBe(false);
    expect(canEditMemberRole('admin', 'owner', 2)).toBe(false);
  });

  it('prevents last-owner removal', () => {
    expect(canRemoveMember('owner', 'owner', 1)).toBe(false);
    expect(canRemoveMember('owner', 'owner', 2)).toBe(true);
    expect(canRemoveMember('owner', 'owner')).toBe(false);
    expect(canRemoveMember('admin', 'owner', 2)).toBe(false);
  });
});
