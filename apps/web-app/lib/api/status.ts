import type { PlatformStatusSnapshot, RawPlatformStatusResponse } from '@/types/status';
import { mapPlatformStatusResponse } from '@/types/status';

interface PlatformStatusApiResponse {
  success: boolean;
  status?: RawPlatformStatusResponse;
  error?: string;
}

const STATUS_FETCH_ERROR = 'Unable to load platform status.';

async function parseJson(response: Response): Promise<PlatformStatusApiResponse> {
  try {
    return (await response.json()) as PlatformStatusApiResponse;
  } catch (_error) {
    return { success: false, error: STATUS_FETCH_ERROR };
  }
}

function createStatusError(message?: string): Error {
  return new Error(message ?? STATUS_FETCH_ERROR);
}

export async function fetchPlatformStatusSnapshot(): Promise<PlatformStatusSnapshot> {
  const response = await fetch('/api/status', { cache: 'no-store' });
  const payload = await parseJson(response);

  if (!response.ok || payload.success !== true || !payload.status) {
    throw createStatusError(payload.error);
  }

  return mapPlatformStatusResponse(payload.status);
}
