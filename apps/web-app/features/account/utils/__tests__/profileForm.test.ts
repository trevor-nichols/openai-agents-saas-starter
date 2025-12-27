import { buildProfilePatch, createProfileFormValues } from '../profileForm';

const baseProfile = {
  user_id: 'user-1',
  tenant_id: 'tenant-1',
  email: 'owner@example.com',
  role: 'owner',
  email_verified: true,
} as const;

describe('createProfileFormValues', () => {
  it('returns empty strings when profile is missing', () => {
    expect(createProfileFormValues(null)).toEqual({
      displayName: '',
      givenName: '',
      familyName: '',
      avatarUrl: '',
      timezone: '',
      locale: '',
    });
  });

  it('maps profile fields into form values', () => {
    const values = createProfileFormValues({
      ...baseProfile,
      display_name: 'Ava',
      given_name: 'Ava',
      family_name: 'Cole',
      avatar_url: 'https://example.com/avatar.png',
      timezone: 'America/Chicago',
      locale: 'en-US',
    });

    expect(values).toEqual({
      displayName: 'Ava',
      givenName: 'Ava',
      familyName: 'Cole',
      avatarUrl: 'https://example.com/avatar.png',
      timezone: 'America/Chicago',
      locale: 'en-US',
    });
  });
});

describe('buildProfilePatch', () => {
  it('includes only dirty fields', () => {
    const patch = buildProfilePatch(
      {
        displayName: '  Nova  ',
        givenName: 'Nora',
        familyName: '',
        avatarUrl: '',
        timezone: 'America/New_York',
        locale: 'en-US',
      },
      { displayName: true, timezone: true },
    );

    expect(patch).toEqual({
      display_name: 'Nova',
      timezone: 'America/New_York',
    });
  });

  it('clears fields when dirty and empty', () => {
    const patch = buildProfilePatch(
      {
        displayName: '',
        givenName: '',
        familyName: '  ',
        avatarUrl: '  ',
        timezone: '',
        locale: '',
      },
      { familyName: true, avatarUrl: true },
    );

    expect(patch).toEqual({
      family_name: null,
      avatar_url: null,
    });
  });
});
