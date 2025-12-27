import type {
  CurrentUserProfileResponseData,
  UserProfileUpdateRequest,
} from '@/lib/api/client/types.gen';

export type ProfileFormValues = {
  displayName: string;
  givenName: string;
  familyName: string;
  avatarUrl: string;
  timezone: string;
  locale: string;
};

export function createProfileFormValues(
  profile?: CurrentUserProfileResponseData | null,
): ProfileFormValues {
  return {
    displayName: profile?.display_name ?? '',
    givenName: profile?.given_name ?? '',
    familyName: profile?.family_name ?? '',
    avatarUrl: profile?.avatar_url ?? '',
    timezone: profile?.timezone ?? '',
    locale: profile?.locale ?? '',
  };
}

function normalizeOptional(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export function buildProfilePatch(
  values: ProfileFormValues,
  dirtyFields: Partial<Record<keyof ProfileFormValues, boolean>>,
): UserProfileUpdateRequest {
  const patch: UserProfileUpdateRequest = {};
  if (dirtyFields.displayName) patch.display_name = normalizeOptional(values.displayName);
  if (dirtyFields.givenName) patch.given_name = normalizeOptional(values.givenName);
  if (dirtyFields.familyName) patch.family_name = normalizeOptional(values.familyName);
  if (dirtyFields.avatarUrl) patch.avatar_url = normalizeOptional(values.avatarUrl);
  if (dirtyFields.timezone) patch.timezone = normalizeOptional(values.timezone);
  if (dirtyFields.locale) patch.locale = normalizeOptional(values.locale);
  return patch;
}
