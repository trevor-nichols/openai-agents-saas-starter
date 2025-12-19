'use server';

import { getCurrentUserProfileApiV1UsersMeGet } from '@/lib/api/client/sdk.gen';
import type {
  CurrentUserProfileResponseData,
  CurrentUserProfileSuccessResponse,
} from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../apiClient';

export async function getCurrentUserProfile(): Promise<CurrentUserProfileResponseData | null> {
  const { client, auth } = await getServerApiClient();
  const response = await getCurrentUserProfileApiV1UsersMeGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
  });

  const payload = response.data as CurrentUserProfileSuccessResponse | undefined;
  const data = (payload?.data ?? null) as CurrentUserProfileResponseData | null;

  if (payload?.success === false) {
    throw new Error(payload.message ?? 'Unable to load current user profile.');
  }

  return data;
}
