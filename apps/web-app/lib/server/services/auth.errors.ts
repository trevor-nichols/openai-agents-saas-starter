import 'server-only';
import type { MfaChallengeResponse } from '@/lib/api/client/types.gen';

export class MfaRequiredError extends Error {
  constructor(public readonly payload: MfaChallengeResponse) {
    super('Multi-factor authentication required');
  }
}
