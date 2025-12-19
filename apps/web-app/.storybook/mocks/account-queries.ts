import type { AccountProfileData } from '@/types/account';
import { mockAccountProfile } from './account-fixtures';

type ProfileState = 'default' | 'loading' | 'error' | 'verified';

let profileState: ProfileState = 'default';
let profileData: AccountProfileData = mockAccountProfile;

export function setAccountProfileState(next: ProfileState, overrides?: Partial<AccountProfileData>) {
  profileState = next;
  if (overrides) {
    profileData = { ...mockAccountProfile, ...overrides };
  }
}

export function useAccountProfileQuery() {
  if (profileState === 'loading') {
    return {
      profile: null,
      tenantError: null,
      isLoadingProfile: true,
      profileError: null,
      refetchProfile: async () => {},
    };
  }

  if (profileState === 'error') {
    return {
      profile: null,
      tenantError: null,
      isLoadingProfile: false,
      profileError: new Error('Unable to load profile (storybook mock).'),
      refetchProfile: async () => {},
    };
  }

  const profile =
    profileState === 'verified'
      ? { ...profileData, verification: { emailVerified: true } }
      : profileData;

  return {
    profile,
    tenantError: null,
    isLoadingProfile: false,
    profileError: null,
    refetchProfile: async () => {},
  };
}

export function useResendVerificationMutation() {
  return {
    isPending: false,
    mutateAsync: async () => {},
  };
}
