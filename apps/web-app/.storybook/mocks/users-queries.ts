import type { CurrentUserProfileResponseData } from '@/lib/api/client/types.gen';

const mockProfile: CurrentUserProfileResponseData = {
  user_id: 'user_123',
  tenant_id: 'tenant_123',
  email: 'ava@acme.com',
  display_name: 'Ava Hart',
  given_name: 'Ava',
  family_name: 'Hart',
  avatar_url: null,
  timezone: 'America/Chicago',
  locale: 'en-US',
  role: 'owner',
  email_verified: false,
};

type ProfileState = 'default' | 'loading' | 'error' | 'verified';

let profileState: ProfileState = 'default';
let profileData: CurrentUserProfileResponseData = mockProfile;

export function setCurrentUserProfileState(next: ProfileState, overrides?: Partial<CurrentUserProfileResponseData>) {
  profileState = next;
  if (overrides) {
    profileData = { ...mockProfile, ...overrides };
  }
}

export function useCurrentUserProfileQuery() {
  if (profileState === 'loading') {
    return {
      profile: null,
      isLoadingProfile: true,
      profileError: null,
      refetchProfile: async () => {},
    };
  }

  if (profileState === 'error') {
    return {
      profile: null,
      isLoadingProfile: false,
      profileError: new Error('Unable to load user profile (storybook mock).'),
      refetchProfile: async () => {},
    };
  }

  const profile =
    profileState === 'verified'
      ? { ...profileData, email_verified: true }
      : profileData;

  return {
    profile,
    isLoadingProfile: false,
    profileError: null,
    refetchProfile: async () => {},
  };
}

export function useUpdateCurrentUserProfileMutation() {
  return {
    isPending: false,
    mutateAsync: async () => profileData,
  };
}

export function useChangeCurrentUserEmailMutation() {
  return {
    isPending: false,
    mutateAsync: async (payload: { new_email: string }) => ({
      user_id: profileData.user_id,
      email: payload.new_email,
      email_verified: false,
      verification_sent: true,
    }),
  };
}

export function useDisableCurrentUserAccountMutation() {
  return {
    isPending: false,
    mutateAsync: async () => ({
      user_id: profileData.user_id,
      disabled: true,
      revoked_sessions: 1,
    }),
  };
}
